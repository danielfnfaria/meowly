from collections.abc import Mapping

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from meowly_contracts import (
    COMPONENT_LABEL,
    TASK_LABEL,
    NotFoundError,
    PlatformTask,
    TaskKind,
    TaskSpec,
)
from meowly_core import Component, InMemoryTaskStore, Owner, build_core
from meowly_core.repositories import ComponentRepository, OwnerRepository


def _spec(component: str | None = None) -> TaskSpec:
    return TaskSpec(kind=TaskKind.NOOP, requested_by="me", component=component)


async def test_in_memory_store() -> None:
    store = InMemoryTaskStore()
    created = await store.create(_spec(), name="task-1")
    assert created.name == "task-1"
    assert await store.get("task-1") == created
    assert await store.list() == [created]
    with pytest.raises(NotFoundError):
        await store.get("nope")


class RecordingStore(InMemoryTaskStore):
    def __init__(self) -> None:
        super().__init__()
        self.labels: dict[str, str] = {}

    async def create(
        self,
        spec: TaskSpec,
        *,
        name: str | None = None,
        labels: Mapping[str, str] | None = None,
    ) -> PlatformTask:
        self.labels = dict(labels or {})
        return await super().create(spec, name=name, labels=labels)


async def _catalog(session: AsyncSession, *, component: str = "svc") -> None:
    """A component the task can legitimately point at."""
    owner = await OwnerRepository(session).add(Owner(slug="team-a", name="Team A"))
    await ComponentRepository(session).add(
        Component(slug=component, name=component.upper(), owner_id=owner.id)
    )


async def test_service_names_and_labels(session: AsyncSession) -> None:
    store = RecordingStore()
    await _catalog(session)
    core = build_core(session, tasks=store)
    service = core.tasks

    task = await service.create(_spec("svc"))
    assert task.name.startswith("task-") and len(task.name) == len("task-") + 10
    assert store.labels == {TASK_LABEL: task.name, COMPONENT_LABEL: "svc"}
    await service.create(_spec())
    assert COMPONENT_LABEL not in store.labels
    assert len(await service.list()) == 2
    assert (await service.get(task.name)).name == task.name
    with pytest.raises(NotFoundError):
        await service.get("missing")


async def test_a_task_cannot_point_at_a_catalog_entry_that_does_not_exist(
    session: AsyncSession,
) -> None:
    # The worker cannot read the catalog (ADR 0002), so an unknown slug would only surface as
    # a failed pod. It is refused at creation instead.
    core = build_core(session, tasks=InMemoryTaskStore())
    with pytest.raises(NotFoundError):
        await core.tasks.create(_spec("nope"))
    with pytest.raises(NotFoundError):
        await core.tasks.create(TaskSpec(kind=TaskKind.NOOP, requested_by="me", template="missing"))
    assert await core.tasks.list() == []
