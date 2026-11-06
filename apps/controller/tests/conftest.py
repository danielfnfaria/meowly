from datetime import UTC, datetime, timedelta

import kopf
import pytest

from meowly_contracts import (
    JsonDict,
    PlatformTask,
    TaskKind,
    TaskPhase,
    TaskSpec,
    TaskStatus,
    task_body,
)
from meowly_controller.adapters.memory import MemoryKube
from meowly_controller.handlers import Runtime
from meowly_controller.settings import Settings

WORKER_IMAGE = "registry.example/meowly-worker:abc"
UID = "7b6c1d2e-0000-0000-0000-000000000001"


@pytest.fixture
def settings() -> Settings:
    return Settings(
        worker_image=WORKER_IMAGE,
        execution_namespace="meowly-test",
        worker_service_account="meowly-worker-sa",
        task_ttl_seconds=600,
        job_active_deadline_seconds=300,
        job_backoff_limit=2,
    )


@pytest.fixture
def kube() -> MemoryKube:
    return MemoryKube()


@pytest.fixture
def memo(settings: Settings, kube: MemoryKube) -> kopf.Memo:
    memo = kopf.Memo()
    memo["runtime"] = Runtime(settings=settings, kube=kube)
    return memo


def make_body(
    name: str = "task-1", *, status: TaskStatus | None = None, component: str | None = "checkout"
) -> JsonDict:
    spec = TaskSpec(kind=TaskKind.NOOP, component=component, requested_by="daniel")
    body = task_body(name, namespace="meowly-test", spec=spec)
    body["metadata"]["uid"] = UID
    if status is not None:
        body["status"] = status.model_dump(mode="json")
    return body


def stored(kube: MemoryKube, body: JsonDict) -> PlatformTask:
    """Put the CR in the fake cluster, as the API server would hold it."""
    from meowly_contracts import task_from_body

    task = task_from_body(body)
    kube.tasks[task.name] = task
    return task


def finished_status(phase: TaskPhase = TaskPhase.SUCCEEDED, **extra: object) -> TaskStatus:
    return TaskStatus(
        phase=phase,
        started_at=datetime.now(UTC),
        finished_at=datetime.now(UTC),
        **extra,  # pyright: ignore[reportArgumentType]
    )


def old(seconds: int) -> datetime:
    return datetime.now(UTC) - timedelta(seconds=seconds)
