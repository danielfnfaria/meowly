"""The worker's progress stream: one JSON object per stdout line (JSONL).

The pod's stdout *is* the task log (ADR 0002), so the worker writes nothing else to it: its
own logs go to stderr. The controller and the API read these lines back.
"""

import json
from datetime import UTC, datetime
from enum import StrEnum
from typing import Final

from pydantic import Field, ValidationError

from meowly_contracts._base import Model
from meowly_contracts.task import TaskStatus


class TaskEventType(StrEnum):
    STARTED = "started"
    STEP = "step"
    LOG = "log"
    FINISHED = "finished"


class TaskEvent(Model):
    """One line of the stream. `seq` starts at 1 and never repeats within a task."""

    seq: int = Field(ge=1)
    ts: datetime = Field(default_factory=lambda: datetime.now(UTC))
    type: TaskEventType
    message: str = ""
    data: dict[str, str] = Field(default_factory=dict[str, str])


def encode_event(event: TaskEvent) -> str:
    """The event as the single line the worker prints (no trailing newline)."""
    return event.model_dump_json()


def decode_event(line: str) -> TaskEvent | None:
    """A stdout line back into an event, or None when the line is not one.

    A pod's stdout can carry anything a dependency decided to print; a reader skips what it
    does not recognise instead of failing the task.
    """
    stripped = line.strip()
    if not stripped:
        return None
    try:
        payload = json.loads(stripped)
    except ValueError:
        return None
    if not isinstance(payload, dict):
        return None
    try:
        return TaskEvent.model_validate(payload)
    except ValidationError:
        return None


_STATUS_KEY: Final = "status"
"""Key of a FINISHED event's `data` that carries the final `TaskStatus` as JSON."""


def finished_data(status: TaskStatus) -> dict[str, str]:
    """The `data` of the FINISHED event that reports `status`.

    The worker writes that event and the controller reads it back, and neither may import the
    other's package (ADR 0003). So the convention lives here, next to `status_from_event`,
    instead of as the same string literal maintained on both sides of the boundary.
    """
    return {_STATUS_KEY: status.model_dump_json()}


def status_from_event(event: TaskEvent) -> TaskStatus | None:
    """The status a FINISHED event reports, or None for any other event, for a FINISHED one
    that carries no status, and for a payload this version cannot read."""
    if event.type is not TaskEventType.FINISHED:
        return None
    payload = event.data.get(_STATUS_KEY)
    if payload is None:
        return None
    try:
        return TaskStatus.model_validate_json(payload)
    except ValidationError:
        return None
