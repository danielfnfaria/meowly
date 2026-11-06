"""Domain errors. Every one carries a stable `code` (what a client matches on) and a
`message` safe to show; `meowly_http.errors` is the single place that maps them to HTTP.
"""


class MeowlyError(Exception):
    """Base of every domain error. `code` is stable API, `message` is for humans."""

    code = "error"

    def __init__(self, message: str, *, code: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        if code is not None:
            self.code = code


class ValidationError(MeowlyError):
    code = "validation_error"


class PayloadTooLargeError(ValidationError):
    code = "payload_too_large"


class NotFoundError(MeowlyError):
    code = "not_found"


class ConflictError(MeowlyError):
    code = "conflict"


class AuthenticationError(MeowlyError):
    code = "unauthenticated"


class PermissionDeniedError(MeowlyError):
    code = "permission_denied"


class UpstreamError(MeowlyError):
    """A system meowly depends on (Kubernetes, git, a provider) answered badly."""

    code = "upstream_error"


class UnavailableError(MeowlyError):
    """The capability exists in the product but this deployment was not wired with it."""

    code = "unavailable"
