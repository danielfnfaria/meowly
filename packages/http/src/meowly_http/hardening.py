"""What every HTTP process gets for free: body limit, access log, security headers, errors."""

import time

import structlog
import uvicorn
from fastapi import FastAPI
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from meowly_contracts import PayloadTooLargeError
from meowly_http.errors import error_response, install_error_handlers, status_for

_log = structlog.get_logger("meowly.http")


class BodyLimitMiddleware:
    """Refuses a request body above `max_bytes`.

    Pure ASGI (not `BaseHTTPMiddleware`) so the body is never buffered here. A declared
    Content-Length is refused before the app runs; a chunked body is counted as the app reads
    it and the error is raised inside the app, where the error handlers catch it.
    """

    def __init__(self, app: ASGIApp, max_bytes: int) -> None:
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        error = PayloadTooLargeError(f"request body exceeds {self.max_bytes} bytes")
        declared = dict(scope["headers"]).get(b"content-length")
        if declared is not None and declared.isdigit() and int(declared) > self.max_bytes:
            # Outside the router, so the handlers do not apply: answer with the same table.
            response = JSONResponse(error_response(error), status_code=status_for(error))
            await response(scope, receive, send)
            return

        received = 0

        async def limited_receive() -> Message:
            nonlocal received
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > self.max_bytes:
                    raise error
            return message

        await self.app(scope, limited_receive, send)


class AccessLogMiddleware:
    """One structured line per request: method, path, status, duration_ms."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        started = time.perf_counter()
        status = 500  # what the client gets if the app dies before it answers

        async def logging_send(message: Message) -> None:
            nonlocal status
            if message["type"] == "http.response.start":
                status = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, logging_send)
        finally:
            _log.info(
                "http_request",
                method=scope["method"],
                path=scope["path"],
                status=status,
                duration_ms=round((time.perf_counter() - started) * 1000, 2),
            )


class SecurityHeadersMiddleware:
    def __init__(self, app: ASGIApp, *, public: bool) -> None:
        self.app = app
        self.headers: list[tuple[bytes, bytes]] = [
            (b"x-content-type-options", b"nosniff"),
            (b"referrer-policy", b"no-referrer"),
        ]
        # Only worth sending where a browser can reach the service; an internal one is never
        # framed.
        if public:
            self.headers.append((b"x-frame-options", b"DENY"))

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def secured_send(message: Message) -> None:
            if message["type"] == "http.response.start":
                message.setdefault("headers", [])
                present = {name.lower() for name, _ in message["headers"]}
                message["headers"].extend(h for h in self.headers if h[0] not in present)
            await send(message)

        await self.app(scope, receive, secured_send)


def install(app: FastAPI, *, public: bool, max_body_bytes: int | None) -> None:
    """Wire the shared HTTP behaviour onto `app`."""
    install_error_handlers(app)
    # add_middleware puts the last one added outermost: the access log wraps everything, so
    # it also sees the 413 and the headers of every answer.
    if max_body_bytes is not None:
        app.add_middleware(BodyLimitMiddleware, max_bytes=max_body_bytes)
    app.add_middleware(SecurityHeadersMiddleware, public=public)
    app.add_middleware(AccessLogMiddleware)


def serve(factory: str, *, host: str, port: int, shutdown_timeout_seconds: int) -> None:
    """Run uvicorn on an app factory (`"package.module:create_app"`).

    The graceful timeout is what lets in-flight requests finish when Kubernetes sends SIGTERM.
    """
    uvicorn.run(
        factory,
        factory=True,
        host=host,
        port=port,
        timeout_graceful_shutdown=shutdown_timeout_seconds,
        # The access log is ours (structured, in AccessLogMiddleware).
        access_log=False,
    )
