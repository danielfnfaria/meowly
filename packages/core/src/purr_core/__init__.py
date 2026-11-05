"""The catalog (Postgres) and the dispatch of tasks (Kubernetes).

Imports neither the engine nor the HTTP package (import-linter keeps it that way).
"""

from purr_core.adapters import InMemoryTaskStore, KubernetesTaskStore
from purr_core.composition import Core, build_core, build_task_store
from purr_core.db import Database
from purr_core.models import Base, Component, Environment, Owner, Template
from purr_core.ports import TaskStore
from purr_core.services import (
    ComponentService,
    EnvironmentService,
    OwnerService,
    TaskService,
    TemplateService,
)
from purr_core.settings import CoreSettings

__all__ = [
    "Base",
    "Component",
    "ComponentService",
    "Core",
    "CoreSettings",
    "Database",
    "Environment",
    "EnvironmentService",
    "InMemoryTaskStore",
    "KubernetesTaskStore",
    "Owner",
    "OwnerService",
    "TaskService",
    "TaskStore",
    "Template",
    "TemplateService",
    "build_core",
    "build_task_store",
]
