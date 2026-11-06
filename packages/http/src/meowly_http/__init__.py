"""HTTP plumbing shared by every meowly process that serves HTTP (today: the API)."""

from meowly_http.app import app_lifespan, build_app, run_server
from meowly_http.bearer import bearer_token
from meowly_http.errors import error_response, install_error_handlers, status_for
from meowly_http.hardening import install, serve
from meowly_http.health import health_routes

__all__ = [
    "app_lifespan",
    "bearer_token",
    "build_app",
    "error_response",
    "health_routes",
    "install",
    "install_error_handlers",
    "run_server",
    "serve",
    "status_for",
]
