"""HTTP plumbing shared by every purr process that serves HTTP (today: the API)."""

from purr_http.app import app_lifespan, build_app, run_server
from purr_http.bearer import bearer_token
from purr_http.errors import error_response, install_error_handlers, status_for
from purr_http.hardening import install, serve
from purr_http.health import health_routes

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
