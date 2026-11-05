"""What a task is on the wire: the spec the API resolves and the status the worker reports."""

from datetime import datetime

from pydantic import Field

from purr_contracts._base import Model
from purr_contracts.enums import TaskKind, TaskPhase
from purr_contracts.version import SPEC_VERSION


class TaskSpec(Model):
    """A task fully resolved: the worker needs nothing else to run it (no catalog lookup, no
    database). What the API resolves at creation time is what runs, even if the catalog
    changes afterwards (ADR 0002)."""

    spec_version: int = SPEC_VERSION
    kind: TaskKind
    # Slug of the catalog component the task acts on, when it acts on one.
    component: str | None = None
    # Slug of the template a `scaffold` task renders.
    template: str | None = None
    inputs: dict[str, str] = Field(default_factory=dict[str, str])
    requested_by: str
    # Propagated to the worker pod so one trace covers API -> controller -> pod.
    trace_id: str | None = None


class TaskStatus(Model):
    """Where a task is. Written by the controller onto the CR's `status` subresource; the
    API only reads it."""

    phase: TaskPhase = TaskPhase.PENDING
    message: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    outputs: dict[str, str] = Field(default_factory=dict[str, str])
    error: str | None = None

    @property
    def terminal(self) -> bool:
        return self.phase.terminal
