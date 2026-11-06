"""The versioned surface: every router under `/v1`."""

from fastapi import APIRouter

from meowly_api.api import components, environments, info, owners, tasks, templates
from meowly_api.api import docs as docs_routes
from meowly_api.schemas.base import ErrorOut

# The error responses every route can produce. 422 is declared too: FastAPI would otherwise
# document its own `HTTPValidationError`, which is not what the exception handler returns.
ERROR_RESPONSES: dict[int | str, dict[str, object]] = {
    404: {"model": ErrorOut, "description": "The addressed object does not exist"},
    409: {"model": ErrorOut, "description": "A slug that is already taken"},
    422: {"model": ErrorOut, "description": "The request body is not valid"},
    502: {
        "model": ErrorOut,
        "description": "Kubernetes or another system meowly depends on failed",
    },
}

v1 = APIRouter(prefix="/v1", responses=ERROR_RESPONSES)
v1.include_router(info.router)
v1.include_router(owners.router)
v1.include_router(components.router)
v1.include_router(templates.router)
v1.include_router(environments.router)
v1.include_router(tasks.router)
v1.include_router(docs_routes.router)

__all__ = ["v1"]
