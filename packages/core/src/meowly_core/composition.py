from dataclasses import dataclass
from typing import Literal

from sqlalchemy.ext.asyncio import AsyncSession

from meowly_core.adapters import InMemoryTaskStore, KubernetesTaskStore
from meowly_core.ports import TaskStore
from meowly_core.repositories import (
    ComponentRepository,
    EnvironmentRepository,
    OwnerRepository,
    TemplateRepository,
)
from meowly_core.services import (
    ComponentService,
    EnvironmentService,
    OwnerService,
    TaskService,
    TemplateService,
)


@dataclass(frozen=True)
class Core:
    """The services of one unit of work (one session)."""

    components: ComponentService
    owners: OwnerService
    templates: TemplateService
    environments: EnvironmentService
    tasks: TaskService


def build_core(session: AsyncSession, *, tasks: TaskStore) -> Core:
    owners = OwnerRepository(session)
    components = ComponentRepository(session)
    templates = TemplateRepository(session)
    return Core(
        components=ComponentService(components, owners),
        owners=OwnerService(owners),
        templates=TemplateService(templates),
        environments=EnvironmentService(EnvironmentRepository(session)),
        tasks=TaskService(tasks, components, templates),
    )


def build_task_store(*, launcher: Literal["kubernetes", "memory"], namespace: str) -> TaskStore:
    if launcher == "memory":
        return InMemoryTaskStore(namespace)
    return KubernetesTaskStore(namespace)
