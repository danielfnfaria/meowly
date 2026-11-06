from datetime import datetime
from typing import Self

from pydantic import Field

from meowly_api.schemas.base import Body, Out
from meowly_contracts import PlatformTask, TaskKind, TaskPhase


class TaskCreate(Body):
    """A request to run something. `requested_by` is not here: it is not the client's to claim
    (there is no authentication yet), the API sets it."""

    kind: TaskKind
    component: str | None = None
    template: str | None = None
    inputs: dict[str, str] = Field(default_factory=dict[str, str])
    trace_id: str | None = None


class TaskOut(Out):
    name: str
    kind: TaskKind
    phase: TaskPhase
    message: str | None
    component: str | None
    template: str | None
    requested_by: str
    outputs: dict[str, str]
    error: str | None
    started_at: datetime | None
    finished_at: datetime | None

    @classmethod
    def from_task(cls, task: PlatformTask) -> Self:
        """A `PlatformTask` whose controller may not have written a status yet reads as pending."""
        status = task.phase_or_pending
        return cls(
            name=task.name,
            kind=task.spec.kind,
            phase=status.phase,
            message=status.message,
            component=task.spec.component,
            template=task.spec.template,
            requested_by=task.spec.requested_by,
            outputs=status.outputs,
            error=status.error,
            started_at=status.started_at,
            finished_at=status.finished_at,
        )
