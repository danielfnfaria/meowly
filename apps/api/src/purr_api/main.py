from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

import structlog
from fastapi import FastAPI

from purr_api.api import health, v1
from purr_api.api.deps import AppState
from purr_api.api.ui import ui_router
from purr_api.settings import ServerSettings, Settings, get_settings
from purr_core import Database, build_task_store
from purr_http import app_lifespan, build_app, run_server
from purr_runtime import configure_logging

log = structlog.get_logger(__name__)


def _production_state(cfg: Settings) -> AppState:
    """The process state over the real adapters; tests inject theirs instead."""
    return AppState(
        settings=cfg,
        db=Database.from_settings(cfg),
        tasks=build_task_store(launcher=cfg.launcher, namespace=cfg.execution_namespace),
    )


def _include_ui(app: FastAPI, ui_dir: str | None) -> None:
    """Serve the UI build when it is there. Last: its catch-all route must not shadow /v1 or
    /healthz."""
    if ui_dir and (Path(ui_dir) / "index.html").is_file():
        app.include_router(ui_router(Path(ui_dir)))
    else:
        log.warning("ui.missing", ui_dir=ui_dir, detail="no index.html: serving the API only")


def create_app(settings: Settings | None = None, *, state: AppState | None = None) -> FastAPI:
    """App factory. Tests pass a prebuilt `state` with in-memory adapters.

    Migrations are not run here: the chart's `migrate` init container and the compose
    `command` run `alembic upgrade head` before the process starts.
    """
    cfg = state.settings if state is not None else (settings or get_settings())

    @asynccontextmanager
    async def startup(app: FastAPI) -> AsyncGenerator[None]:
        # run_server does not configure logging; the process does it once, here.
        configure_logging(cfg.log_level)
        container = _production_state(cfg)
        app.state.container = container
        log.info("api.started", launcher=cfg.launcher, execution_namespace=cfg.execution_namespace)
        try:
            yield
        finally:
            await container.tasks.close()
            await container.db.dispose()

    app = build_app(
        "purr API",
        version="0.1.0",
        lifespan=app_lifespan(state, startup),
        # Internal tool behind an internal ingress; no browser-facing hardening headers.
        public=False,
        max_body_bytes=cfg.max_body_bytes,
        container=state,
    )
    app.router.routes.extend(health.routes)
    app.include_router(v1)
    _include_ui(app, cfg.ui_dir)
    return app


def run() -> None:
    """Console entrypoint used by the container image."""
    run_server("purr_api.main:create_app", ServerSettings)
