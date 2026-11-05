"""Process plumbing shared by every purr process: JSON logging and the bind settings.

A leaf: structlog + pydantic-settings, no workspace package (import-linter keeps it that way).
"""

from purr_runtime.logging import DEFAULT_QUIET_LOGGERS, configure_logging
from purr_runtime.settings import ServerSettings, cached_settings

__all__ = ["DEFAULT_QUIET_LOGGERS", "ServerSettings", "cached_settings", "configure_logging"]
