from collections.abc import Callable
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ServerSettings(BaseSettings):
    """Where uvicorn listens (PURR_HOST / PURR_PORT) and how long it waits on SIGTERM
    (PURR_SHUTDOWN_TIMEOUT_SECONDS).

    Kept apart from each app's `Settings` so the server can start without the app's required
    config. A process with another default port subclasses it (the API: 8000).
    """

    model_config = SettingsConfigDict(env_prefix="PURR_", extra="ignore")

    host: str = "0.0.0.0"  # noqa: S104 - the container listens on every interface
    port: int = 8080
    # Grace period on SIGTERM before uvicorn cancels whatever request is still open.
    shutdown_timeout_seconds: int = Field(default=20, ge=1)


def cached_settings[S: BaseSettings](cls: type[S]) -> Callable[[], S]:
    """The `get_settings` of a process: `cls()` read from the environment once, then reused."""

    @lru_cache(maxsize=1)
    def get_settings() -> S:
        return cls()

    return get_settings
