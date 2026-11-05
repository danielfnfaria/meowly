"""Probes. Plain Starlette routes from `purr_http`: out of OpenAPI and out of every dependency."""

import structlog
from sqlalchemy import text
from starlette.requests import Request

from purr_api.api.deps import get_state
from purr_http import health_routes

log = structlog.get_logger(__name__)


async def database_ready(request: Request) -> bool:
    """Ready means the catalog answers. A failure is logged and reported as not ready (503)
    instead of raising, so a down database never turns the probe into a 500."""
    try:
        async with get_state(request).db.engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
    except Exception:
        log.warning("health.database_unavailable", exc_info=True)
        return False
    return True


routes = health_routes(database_ready)
