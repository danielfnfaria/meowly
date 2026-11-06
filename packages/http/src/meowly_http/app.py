from collections.abc import AsyncGenerator, Callable
from contextlib import AbstractAsyncContextManager, asynccontextmanager

from fastapi import FastAPI
from starlette.types import Lifespan

from meowly_http.hardening import install, serve
from meowly_runtime import ServerSettings


def build_app(
    title: str,
    *,
    lifespan: Lifespan[FastAPI],
    public: bool,
    max_body_bytes: int | None,
    container: object | None,
    version: str | None = None,
) -> FastAPI:
    """A FastAPI with the shared hardening installed.

    OpenAPI and the docs are off here: the API serves its own under `/v1`, so the generated
    routes would sit at the root, outside the versioned surface. `container` is whatever the
    process wires its dependencies into; it is kept on `app.state` for the dependencies.
    """
    app = FastAPI(
        title=title,
        version=version or "0.0.0",
        lifespan=lifespan,
        openapi_url=None,
        docs_url=None,
        redoc_url=None,
    )
    install(app, public=public, max_body_bytes=max_body_bytes)
    if container is not None:
        app.state.container = container
    return app


def app_lifespan(
    container: object | None,
    startup: Callable[[FastAPI], AbstractAsyncContextManager[None]],
) -> Lifespan[FastAPI]:
    """The lifespan: runs `startup` (build and tear down the real wiring) unless a container
    was handed in already, which is how tests inject theirs."""

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
        if container is not None:
            yield
            return
        async with startup(app):
            yield

    return lifespan


def run_server(factory: str, settings: type[ServerSettings] = ServerSettings) -> None:
    """Entry point of a process: bind settings from the environment, then uvicorn."""
    cfg = settings()
    serve(
        factory,
        host=cfg.host,
        port=cfg.port,
        shutdown_timeout_seconds=cfg.shutdown_timeout_seconds,
    )
