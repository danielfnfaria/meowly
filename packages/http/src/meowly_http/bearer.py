from starlette.requests import Request

from meowly_contracts import AuthenticationError

_SCHEME = "bearer"


def bearer_token(request: Request) -> str:
    """The token of `Authorization: Bearer <token>`.

    Raises `AuthenticationError(code="invalid_token")` when the header is absent or is not a
    well-formed bearer credential; the error handler turns it into a 401 with the challenge.
    """
    header = request.headers.get("authorization", "")
    scheme, _, token = header.partition(" ")
    token = token.strip()
    if scheme.lower() != _SCHEME or not token or " " in token:
        raise AuthenticationError("missing or malformed bearer token", code="invalid_token")
    return token
