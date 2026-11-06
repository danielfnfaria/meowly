"""The catalog (Postgres) and the dispatch of tasks (Kubernetes).

Imports neither the engine nor the HTTP package (import-linter keeps it that way).
"""

from meowly_core.adapters import InMemoryTaskStore, KubernetesTaskStore
from meowly_core.composition import Core, build_core, build_task_store
from meowly_core.db import Database
from meowly_core.models import Base, Component, Environment, Owner, Template
from meowly_core.ports import TaskStore
from meowly_core.services import (
    ComponentService,
    EnvironmentService,
    OwnerService,
    TaskService,
    TemplateService,
)
from meowly_core.settings import CoreSettings

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
