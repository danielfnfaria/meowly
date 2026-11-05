from purr_core import CoreSettings
from purr_runtime import ServerSettings as RuntimeServerSettings
from purr_runtime import cached_settings


class Settings(CoreSettings):
    """The core settings plus what only the API process needs (`PURR_*`)."""

    # Directory with the built UI (`index.html` + assets). Unset or without an index.html, the
    # API serves only itself: that is the state before the UI exists, and in most tests.
    ui_dir: str | None = None
    max_body_bytes: int = 1_048_576


class ServerSettings(RuntimeServerSettings):
    """The API listens on 8000; the runtime default (8080) belongs to the other processes."""

    port: int = 8000


get_settings = cached_settings(Settings)
