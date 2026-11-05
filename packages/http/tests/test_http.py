from collections.abc import AsyncGenerator, AsyncIterator
from contextlib import asynccontextmanager

import httpx
import pytest
from fastapi import FastAPI
from starlette.requests import Request

from purr_contracts import (
    AuthenticationError,
    ConflictError,
    NotFoundError,
    PayloadTooLargeError,
    PermissionDeniedError,
    PurrError,
    UnavailableError,
    UpstreamError,
    ValidationError,
)
from purr_http import app_lifespan, bearer_token, build_app, health_routes, status_for


@asynccontextmanager
async def _no_startup(_: FastAPI) -> AsyncGenerator[None]:
    yield


class SubNotFound(NotFoundError):  # noqa: N818
    pass


class Unmapped(PurrError):  # noqa: N818
    pass


def make_app(
    *, public: bool = True, ready: bool | None = None, max_body: int | None = 10
) -> FastAPI:
    async def check(_: Request) -> bool:
        return bool(ready)

    container = object()
    app = build_app(
        "test",
        lifespan=app_lifespan(container, _no_startup),
        public=public,
        max_body_bytes=max_body,
        container=container,
    )
    app.router.routes.extend(health_routes(check if ready is not None else None))

    @app.post("/echo")
    async def echo(request: Request) -> dict[str, int]:
        return {"size": len(await request.body())}

    @app.get("/boom")
    async def boom() -> None:
        raise ConflictError("already there")

    @app.get("/token")
    async def token(request: Request) -> dict[str, str]:
        return {"token": bearer_token(request)}

    return app


@pytest.fixture
async def client() -> AsyncIterator[httpx.AsyncClient]:
    transport = httpx.ASGITransport(app=make_app())
    async with httpx.AsyncClient(transport=transport, base_url="http://t") as c:
        yield c


async def test_live_and_ready_default(client: httpx.AsyncClient) -> None:
    assert (await client.get("/healthz/live")).json() == {"status": "ok"}
    assert (await client.get("/healthz/ready")).status_code == 200


async def test_ready_false_is_503() -> None:
    transport = httpx.ASGITransport(app=make_app(ready=False))
    async with httpx.AsyncClient(transport=transport, base_url="http://t") as c:
        r = await c.get("/healthz/ready")
        assert r.status_code == 503
        assert r.json() == {"status": "unavailable"}
        assert (await c.get("/healthz/live")).status_code == 200


async def test_ready_true_is_200() -> None:
    transport = httpx.ASGITransport(app=make_app(ready=True))
    async with httpx.AsyncClient(transport=transport, base_url="http://t") as c:
        assert (await c.get("/healthz/ready")).status_code == 200


@pytest.mark.parametrize(
    ("exc", "status"),
    [
        (AuthenticationError("x"), 401),
        (PermissionDeniedError("x"), 403),
        (NotFoundError("x"), 404),
        (SubNotFound("x"), 404),
        (ConflictError("x"), 409),
        (ValidationError("x"), 422),
        (PayloadTooLargeError("x"), 413),
        (UpstreamError("x"), 502),
        (UnavailableError("x"), 501),
        (Unmapped("x"), 500),
        (RuntimeError("x"), 500),
    ],
)
def test_status_for(exc: BaseException, status: int) -> None:
    assert status_for(exc) == status


async def test_domain_error_body(client: httpx.AsyncClient) -> None:
    r = await client.get("/boom")
    assert r.status_code == 409
    assert r.json() == {"code": "conflict", "message": "already there"}


async def test_body_over_limit_is_413(client: httpx.AsyncClient) -> None:
    r = await client.post("/echo", content=b"x" * 11)
    assert r.status_code == 413
    assert r.json()["code"] == "payload_too_large"
    assert "message" in r.json()
    assert (await client.post("/echo", content=b"x" * 10)).json() == {"size": 10}


async def test_streamed_body_over_limit_is_413(client: httpx.AsyncClient) -> None:
    async def chunks() -> AsyncIterator[bytes]:
        for _ in range(3):
            yield b"xxxxx"

    r = await client.post("/echo", content=chunks())
    assert r.status_code == 413
    assert r.json()["code"] == "payload_too_large"


async def test_security_headers_public(client: httpx.AsyncClient) -> None:
    r = await client.get("/healthz/live")
    assert r.headers["x-content-type-options"] == "nosniff"
    assert r.headers["referrer-policy"] == "no-referrer"
    assert r.headers["x-frame-options"] == "DENY"


async def test_security_headers_internal() -> None:
    transport = httpx.ASGITransport(app=make_app(public=False))
    async with httpx.AsyncClient(transport=transport, base_url="http://t") as c:
        r = await c.get("/healthz/live")
        assert r.headers["x-content-type-options"] == "nosniff"
        assert "x-frame-options" not in r.headers


async def test_no_openapi_routes(client: httpx.AsyncClient) -> None:
    for path in ("/openapi.json", "/docs", "/redoc"):
        assert (await client.get(path)).status_code == 404


async def test_bearer_token(client: httpx.AsyncClient) -> None:
    ok = await client.get("/token", headers={"Authorization": "Bearer abc"})
    assert ok.json() == {"token": "abc"}
    for headers in ({}, {"Authorization": "Basic abc"}, {"Authorization": "Bearer"}):
        r = await client.get("/token", headers=headers)
        assert r.status_code == 401
        assert r.json()["code"] == "invalid_token"
        assert r.headers["www-authenticate"].startswith("Bearer")
