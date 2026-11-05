from pydantic_settings import BaseSettings, SettingsConfigDict

from purr_runtime import cached_settings


class Settings(BaseSettings):
    """Read from the environment the chart sets on the controller Deployment."""

    model_config = SettingsConfigDict(env_prefix="PURR_", extra="ignore")

    log_level: str = "INFO"
    # Where PlatformTasks are watched and their Jobs created. The controller has a Role, not a
    # ClusterRole: it cannot see any other namespace.
    execution_namespace: str = "purr"
    worker_image: str
    worker_service_account: str = "purr-worker"
    # How long a finished PlatformTask (and, through its ownerReference, its Job) is kept.
    task_ttl_seconds: int = 86400
    job_active_deadline_seconds: int = 900
    job_backoff_limit: int = 0


get_settings = cached_settings(Settings)
