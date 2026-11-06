"""Run one task from start to finish and describe how it ended."""

from datetime import UTC, datetime

import structlog

from meowly_contracts import (
    MeowlyError,
    TaskEventType,
    TaskPhase,
    TaskSpec,
    TaskStatus,
    finished_data,
)
from meowly_engine.events import EventWriter
from meowly_engine.steps import STEPS

log = structlog.get_logger(__name__)


def execute(spec: TaskSpec, *, writer: EventWriter) -> TaskStatus:
    """Emit STARTED, run the step of `spec.kind`, emit FINISHED and return the final status.

    Nothing escapes: the worker's only way to report is its event stream, so even a bug in a
    step must end as a FAILED status in a FINISHED event rather than as a bare traceback.
    """
    started_at = datetime.now(UTC)
    writer.emit(TaskEventType.STARTED, f"{spec.kind} task started", {})
    try:
        outputs = dict(STEPS[spec.kind](spec, writer.emit))
        status = TaskStatus(phase=TaskPhase.SUCCEEDED, outputs=outputs)
    except MeowlyError as exc:
        status = TaskStatus(phase=TaskPhase.FAILED, error=exc.code, message=exc.message)
    except Exception:
        # The traceback goes to the (stderr) log only: it can name paths and internals that
        # do not belong in a status every reader of the CR can see.
        log.exception("engine.unexpected_error", kind=spec.kind)
        status = TaskStatus(
            phase=TaskPhase.FAILED, error="internal_error", message="the task failed unexpectedly"
        )
    status = status.model_copy(update={"started_at": started_at, "finished_at": datetime.now(UTC)})
    writer.emit(
        TaskEventType.FINISHED,
        status.message or status.phase.value,
        finished_data(status),
    )
    return status
