import uuid
from collections.abc import Mapping

from purr_contracts import NotFoundError, PlatformTask, TaskSpec


class InMemoryTaskStore:
    """Tasks held in the process: `make up` without a cluster, and the tests. Nothing
    reconciles them, so they stay pending."""

    def __init__(self, namespace: str = "purr") -> None:
        self._namespace = namespace
        self._tasks: dict[str, PlatformTask] = {}

    async def create(
        self,
        spec: TaskSpec,
        *,
        name: str | None = None,
        labels: Mapping[str, str] | None = None,
    ) -> PlatformTask:
        # Labels only matter to the cluster's selectors; there is nothing to select here.
        del labels
        task = PlatformTask(
            name=name or f"task-{uuid.uuid4().hex[:10]}", namespace=self._namespace, spec=spec
        )
        self._tasks[task.name] = task
        return task

    async def list(self) -> list[PlatformTask]:
        return list(self._tasks.values())

    async def get(self, name: str) -> PlatformTask:
        try:
            return self._tasks[name]
        except KeyError:
            raise NotFoundError(f"task {name!r} not found", code="task_not_found") from None

    async def close(self) -> None:
        """Nothing is held outside the process."""
