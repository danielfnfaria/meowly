"""PlatformTask create/resume: turn the CR into a Job and mark it running."""

from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any

import kopf
import structlog
from pydantic import ValidationError as ParseError

from meowly_contracts import (
    TaskPhase,
    TaskStatus,
    task_from_body,
)
from meowly_contracts import ValidationError as InvalidTask
from meowly_controller.handlers.job import reconcile_from_job
from meowly_controller.handlers.runtime import runtime_of
from meowly_controller.services.job import job_manifest

log = structlog.get_logger(__name__)


# Registered for `create` and for `resume`: a task that arrived while the controller was down
# (or whose Job creation failed halfway) is picked up on restart. Idempotent.
async def task_created(body: Mapping[str, Any], name: str, memo: kopf.Memo, **_: object) -> None:
    rt = runtime_of(memo)
    try:
        task = task_from_body(body)
    except ParseError as exc:
        # Retrying cannot fix a spec this version does not understand: fail the task.
        now = datetime.now(UTC)
        log.warning("task.invalid", task=name, errors=exc.error_count())
        await rt.kube.patch_task_status(
            name,
            TaskStatus(
                phase=TaskPhase.FAILED,
                error=InvalidTask.code,
                message="the PlatformTask spec is not valid for this version of meowly",
                # The task never ran, so both are the same instant. Without finished_at the
                # TTL prune never expires a terminal task.
                started_at=now,
                finished_at=now,
            ),
        )
        return

    # Re-read: the body kopf hands over can be older than a status the Job handler wrote.
    stored = await rt.kube.get_task(name)
    current = stored.status if stored is not None else task.status
    if current is not None and current.terminal:
        return

    await rt.kube.create_job(job_manifest(task, rt.settings))
    # Not a blind `running`: on a resume the Job may have ended already (the controller died
    # between creating it and writing the status) and no further Job event will come. A new
    # Job reads as active, which is `running`.
    job = await rt.kube.get_job(name)
    await reconcile_from_job(rt, name, job or {})
    log.info("task.job_created", task=name, kind=task.spec.kind)
