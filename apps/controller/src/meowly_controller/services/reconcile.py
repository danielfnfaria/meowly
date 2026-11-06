"""Pure reconciliation: from the Job's state and the pod log to the next `TaskStatus`."""

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from meowly_contracts import TaskPhase, TaskStatus, decode_event, status_from_event


class JobOutcome(StrEnum):
    ACTIVE = "active"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class JobState:
    outcome: JobOutcome
    # Why Kubernetes failed the Job (e.g. DeadlineExceeded), when it said.
    reason: str | None = None


def job_state(job: Mapping[str, Any]) -> JobState:
    """Read a Job object. `status.failed` alone is not final (retries may follow): only the
    `Failed` condition is."""
    status: Mapping[str, Any] = job.get("status") or {}
    conditions: list[Mapping[str, Any]] = status.get("conditions") or []
    for condition in conditions:
        if condition.get("status") != "True":
            continue
        if condition.get("type") == "Complete":
            return JobState(JobOutcome.SUCCEEDED)
        if condition.get("type") == "Failed":
            return JobState(JobOutcome.FAILED, condition.get("reason"))
    if (status.get("succeeded") or 0) > 0:
        return JobState(JobOutcome.SUCCEEDED)
    return JobState(JobOutcome.ACTIVE)


def reported_status(log: str) -> TaskStatus | None:
    """The final status in the last FINISHED event of the pod log, if there is a usable one.

    Lines that are not events (a dependency that printed to stdout, a truncated line) are
    skipped, as are FINISHED events whose payload is not a terminal status.
    """
    found: TaskStatus | None = None
    for line in log.splitlines():
        event = decode_event(line)
        status = status_from_event(event) if event is not None else None
        if status is not None and status.terminal:
            found = status
    return found


def next_status(
    current: TaskStatus | None, state: JobState, log: str, *, now: datetime | None = None
) -> TaskStatus | None:
    """The status to write, or None when there is nothing to write.

    A task already in a terminal phase is never rewritten: the TTL starts from the first
    terminal status, and a late event or a retried handler must not move it.
    """
    now = now or datetime.now(UTC)
    if current is not None and current.terminal:
        return None
    started_at = current.started_at if current and current.started_at else now

    if state.outcome is JobOutcome.ACTIVE:
        if current is not None and current.phase is TaskPhase.RUNNING:
            return None
        return TaskStatus(phase=TaskPhase.RUNNING, started_at=started_at)

    reported = reported_status(log)
    if reported is not None:
        return reported.model_copy(
            update={
                "started_at": reported.started_at or started_at,
                "finished_at": reported.finished_at or now,
            }
        )
    # No result event. A worker exits 0 only after printing one, so a Job that "succeeded"
    # with none means the log is gone (pod garbage-collected): outputs cannot be invented.
    detail = f" ({state.reason})" if state.reason else ""
    return TaskStatus(
        phase=TaskPhase.FAILED,
        error="no_result",
        message=f"the worker pod did not report a result; job {state.outcome.value}{detail}",
        started_at=started_at,
        finished_at=now,
    )


def lost_job_status(current: TaskStatus | None, *, now: datetime | None = None) -> TaskStatus:
    """The terminal status of a running task whose Job no longer exists: nothing will ever
    report on it, so it fails instead of staying `running` forever."""
    now = now or datetime.now(UTC)
    return TaskStatus(
        phase=TaskPhase.FAILED,
        error="job_missing",
        message="the Job of this task disappeared before it reported a result",
        started_at=current.started_at if current and current.started_at else now,
        finished_at=now,
    )


def expired(status: TaskStatus | None, ttl_seconds: int, *, now: datetime) -> bool:
    """Whether a task finished more than `ttl_seconds` ago. A task that is not terminal, or
    has no finish time, is never expired."""
    if status is None or not status.terminal or status.finished_at is None:
        return False
    return (now - status.finished_at).total_seconds() >= ttl_seconds
