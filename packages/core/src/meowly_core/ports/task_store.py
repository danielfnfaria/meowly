from collections.abc import Mapping
from typing import Protocol

from meowly_contracts import PlatformTask, TaskSpec


class TaskStore(Protocol):
    """Where tasks live. The execution is a PlatformTask custom resource, never a database
    row (ADR 0002)."""

    async def create(
        self,
        spec: TaskSpec,
        *,
        name: str | None = None,
        labels: Mapping[str, str] | None = None,
    ) -> PlatformTask:
        """Store the task under `name` (generated when omitted)."""
        ...

    async def list(self) -> list[PlatformTask]: ...

    async def get(self, name: str) -> PlatformTask:
        """Raises `NotFoundError` when no task has that name."""
        ...

    async def close(self) -> None:
        """Release the client held for the cluster (its connection pool); called once at
        shutdown."""
        ...
