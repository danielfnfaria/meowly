"""PlatformTask create/resume: turn the CR into a Job and mark it running."""

from collections.abc import Mapping
from typing import Any

import kopf
import structlog
from pydantic import ValidationError as ParseError

from purr_contracts import (
    TaskPhase,
    TaskStatus,
    task_from_body,
)
from purr_contracts import ValidationError as InvalidTask
from purr_controller.handlers.runtime import runtime_of
from purr_controller.services.job import job_manifest
from purr_controller.services.reconcile import JobOutcome, JobState, next_status

log = structlog.get_logger(__name__)


# Registered for `create` and for `resume`: a task that arrived while the controller was down
# (or whose Job creation failed halfway) is picked up on restart. Idempotent.
async def task_created(body: Mapping[str, Any], name: str, memo: kopf.Memo, **_: object) -> None:
    rt = runtime_of(memo)
    try:
        task = task_from_body(body)
    except ParseError as exc:
        # Retrying cannot fix a spec this version does not understand: fail the task.
        log.warning("task.invalid", task=name, errors=exc.error_count())
        await rt.kube.patch_task_status(
            name,
            TaskStatus(
                phase=TaskPhase.FAILED,
                error=InvalidTask.code,
                message="the PlatformTask spec is not valid for this version of purr",
            ),
        )
        return

    # Re-read: the body kopf hands over can be older than a status the Job handler wrote.
    stored = await rt.kube.get_task(name)
    current = stored.status if stored is not None else task.status
    if current is not None and current.terminal:
        return

    await rt.kube.create_job(job_manifest(task, rt.settings))
    running = next_status(current, JobState(JobOutcome.ACTIVE), "")
    if running is not None:
        await rt.kube.patch_task_status(name, running)
    log.info("task.job_created", task=name, kind=task.spec.kind)
