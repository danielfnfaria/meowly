from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class CoreSettings(BaseSettings):
    """What the catalog and the task dispatch need, from `PURR_*` environment variables."""

    model_config = SettingsConfigDict(env_prefix="PURR_", extra="ignore")

    database_url: str
    log_level: str = "INFO"
    # `memory` keeps tasks in the process (local `make up`, tests): no cluster needed.
    launcher: Literal["kubernetes", "memory"] = "kubernetes"
    execution_namespace: str = "purr"
    worker_image: str = "purr-worker:dev"
    db_pool_size: int = 5
    db_max_overflow: int = 10
