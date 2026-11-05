"""The single table domain error -> HTTP status. Nothing else in the code base picks a status
for a domain error."""

from typing import Any, cast

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

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

# Looked up along the MRO, so a subclass inherits its parent's status unless it has its own
# entry (PayloadTooLargeError is a ValidationError but must answer 413, not 422).
_STATUS: dict[type[BaseException], int] = {
    AuthenticationError: 401,
    PermissionDeniedError: 403,
    NotFoundError: 404,
    ConflictError: 409,
    ValidationError: 422,
    PayloadTooLargeError: 413,
    UpstreamError: 502,
    UnavailableError: 501,
}

INVALID_TOKEN_CODE = "invalid_token"  # noqa: S105 - an error code, not a credential


def status_for(exc: BaseException) -> int:
    """HTTP status for `exc`, resolved by MRO; 500 when no class in it is mapped."""
    for cls in type(exc).__mro__:
        status = _STATUS.get(cls)
        if status is not None:
            return status
    return 500


def error_response(exc: PurrError) -> dict[str, str]:
    """The body every error answers with."""
    return {"code": exc.code, "message": exc.message}


def _purr_error_handler(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, PurrError)
    headers: dict[str, str] | None = None
    # RFC 6750: a 401 on a bearer-protected resource tells the client which scheme to use.
    if isinstance(exc, AuthenticationError):
        headers = {"WWW-Authenticate": "Bearer"}
        if exc.code == INVALID_TOKEN_CODE:
            headers["WWW-Authenticate"] = 'Bearer error="invalid_token"'
    return JSONResponse(error_response(exc), status_code=status_for(exc), headers=headers)


def _request_validation_handler(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, RequestValidationError)
    # Same body shape as every other error; the first problem is enough for a human, the
    # location tells which field.
    problems = cast("list[dict[str, Any]]", exc.errors())
    first: dict[str, Any] = problems[0] if problems else {}
    location = ".".join(str(part) for part in cast("list[Any]", first.get("loc", [])))
    detail = str(first.get("msg", "invalid request"))
    error = ValidationError(f"{location}: {detail}" if location else detail)
    return JSONResponse(error_response(error), status_code=status_for(error))


def install_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(PurrError, _purr_error_handler)
    app.add_exception_handler(RequestValidationError, _request_validation_handler)
