"""The OpenAPI document and the Swagger page, as ordinary `/v1` routes.

`build_app` turns FastAPI's own docs routes off (they would sit at the root, outside the
versioned surface), so they are served from here. `make up` advertises `/v1/docs`.
"""

from fastapi import APIRouter, Request
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse, JSONResponse

OPENAPI_PATH = "/v1/openapi.json"

router = APIRouter(include_in_schema=False)


@router.get("/openapi.json")
async def openapi(request: Request) -> JSONResponse:
    return JSONResponse(request.app.openapi())


@router.get("/docs")
async def docs() -> HTMLResponse:
    return get_swagger_ui_html(openapi_url=OPENAPI_PATH, title="purr API - Swagger UI")
