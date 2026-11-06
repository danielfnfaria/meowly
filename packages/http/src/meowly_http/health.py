from collections.abc import Awaitable, Callable

from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route


def health_routes(ready: Callable[[Request], Awaitable[bool]] | None = None) -> list[Route]:
    """`/healthz/live` and `/healthz/ready` as plain Starlette routes.

    They stay out of the OpenAPI document and out of every dependency: a probe must answer
    even when the app's own wiring is what is broken. Liveness never checks dependencies
    (a down database must not make the kubelet restart the pod); readiness does, via `ready`.
    """

    async def live(_: Request) -> Response:
        return JSONResponse({"status": "ok"})

    async def readiness(request: Request) -> Response:
        if ready is not None and not await ready(request):
            return JSONResponse({"status": "unavailable"}, status_code=503)
        return JSONResponse({"status": "ok"})

    return [
        Route("/healthz/live", live, methods=["GET"]),
        Route("/healthz/ready", readiness, methods=["GET"]),
    ]
