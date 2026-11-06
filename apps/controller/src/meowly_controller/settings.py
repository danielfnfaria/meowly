from typing import cast

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from meowly_runtime import cached_settings


class Settings(BaseSettings):
    """Read from the environment the chart sets on the controller Deployment."""

    model_config = SettingsConfigDict(env_prefix="MEOWLY_", extra="ignore")

    log_level: str = "INFO"
    # Where PlatformTasks are watched and their Jobs created. The controller has a Role, not a
    # ClusterRole: it cannot see any other namespace.
    execution_namespace: str = "meowly"
    worker_image: str
    worker_image_pull_policy: str = "IfNotPresent"
    worker_service_account: str = "meowly-worker"
    # Resources of the worker container as the chart's JSON (`{"requests": {...}, "limits":
    # {...}}`). Empty = none set: the pod is then BestEffort and first to be evicted, so the
    # chart always sets some.
    worker_resources: dict[str, dict[str, str]] = {}

    @field_validator("worker_resources", mode="before")
    @classmethod
    def _quantities_as_strings(cls, value: object) -> object:
        """`cpu: 1` in values.yaml is valid YAML and valid Kubernetes, but reaches here as a
        JSON number. Coerce the quantities instead of refusing to start over a value the
        cluster itself accepts."""
        if not isinstance(value, dict):
            return value
        # Parsed JSON: the keys and values are only known at runtime, hence the casts.
        groups = cast(dict[str, object], value)
        coerced: dict[str, object] = {}
        for group_name, group in groups.items():
            if isinstance(group, dict):
                quantities = cast(dict[str, object], group)
                coerced[group_name] = {name: str(q) for name, q in quantities.items()}
            else:
                coerced[group_name] = group
        return coerced

    # How long a finished PlatformTask (and, through its ownerReference, its Job) is kept.
    task_ttl_seconds: int = 86400
    job_active_deadline_seconds: int = 900
    job_backoff_limit: int = 0


get_settings = cached_settings(Settings)
