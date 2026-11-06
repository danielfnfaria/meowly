from pydantic_settings import BaseSettings, SettingsConfigDict

from meowly_runtime import cached_settings


class Settings(BaseSettings):
    """What the controller injects into the Job's pod (and nothing else: no credentials)."""

    model_config = SettingsConfigDict(env_prefix="MEOWLY_", extra="ignore")

    task_name: str
    # The JSON of the `TaskSpec`, exactly as the API resolved it.
    task_spec: str
    log_level: str = "INFO"


get_settings = cached_settings(Settings)
