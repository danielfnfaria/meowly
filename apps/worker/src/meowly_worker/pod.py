"""The body of the pod: parse the spec, run it, report through stdout."""

import sys
from typing import TextIO

import structlog
from pydantic import ValidationError as SpecParseError

from meowly_contracts import (
    TaskEventType,
    TaskPhase,
    TaskSpec,
    TaskStatus,
    ValidationError,
    finished_data,
)
from meowly_engine import EventWriter, execute
from meowly_runtime import configure_logging
from meowly_worker.settings import Settings

log = structlog.get_logger(__name__)


def run_task(cfg: Settings, *, stdout: TextIO = sys.stdout) -> int:
    """Run the task in `cfg` and return the process exit code (0 only when it succeeded).

    The exit code only tells Kubernetes whether the Job failed; the outcome the controller
    records is the FINISHED event on `stdout`. That is why even a spec that does not parse is
    reported as an event: otherwise the task would fail with no reason attached.
    """
    # stdout is the task's event stream and carries nothing else (ADR 0002).
    configure_logging(cfg.log_level, stream="stderr")
    structlog.contextvars.bind_contextvars(task=cfg.task_name)
    writer = EventWriter(stdout)
    try:
        spec = TaskSpec.model_validate_json(cfg.task_spec)
    except SpecParseError as exc:
        # Field paths and messages only: `input` would echo the spec back, and a spec may
        # carry values that should not land in a status.
        problems = "; ".join(
            f"{'.'.join(str(p) for p in err['loc']) or 'spec'}: {err['msg']}"
            for err in exc.errors(include_url=False, include_context=False, include_input=False)
        )
        log.error("worker.invalid_spec", problems=problems)
        status = TaskStatus(
            phase=TaskPhase.FAILED,
            error=ValidationError.code,
            message=f"invalid task spec: {problems}",
        )
        writer.emit(TaskEventType.FINISHED, status.message or "", finished_data(status))
        return 1
    status = execute(spec, writer=writer)
    log.info("worker.finished", phase=status.phase.value)
    return 0 if status.phase is TaskPhase.SUCCEEDED else 1
