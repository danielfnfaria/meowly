"""Job events: when a meowly Job ends, its task gets the final status."""

from collections.abc import Mapping
from typing import Any

import kopf
import structlog

from meowly_contracts import TASK_LABEL
from meowly_controller.handlers.runtime import Runtime, runtime_of
from meowly_controller.services.reconcile import JobOutcome, job_state, next_status

log = structlog.get_logger(__name__)


async def reconcile_from_job(rt: Runtime, name: str, job: Mapping[str, Any]) -> None:
    """Write the status the Job's current state implies onto task `name`.

    The single path from a Job to a status: the Job event handler, the create handler and the
    timer all go through it, so they cannot disagree. Those handlers run concurrently and
    none of them can assume the others already ran, which is why each one reads the Job
    instead of writing a status blind.
    """
    state = job_state(job)
    task = await rt.kube.get_task(name)
    if task is None:
        return
    # The log is only read once the Job has ended: the final result is in it.
    log_text = await rt.kube.pod_log(name) if state.outcome is not JobOutcome.ACTIVE else ""
    status = next_status(task.status, state, log_text)
    if status is not None:
        await rt.kube.patch_task_status(name, status)
        log.info("task.status", task=name, phase=status.phase.value)


async def job_event(
    body: Mapping[str, Any], event: Mapping[str, Any], memo: kopf.Memo, **_: object
) -> None:
    if event.get("type") == "DELETED":
        return
    labels: Mapping[str, str] = body.get("metadata", {}).get("labels") or {}
    name = labels[TASK_LABEL]
    if job_state(body).outcome is JobOutcome.ACTIVE:
        return  # the create handler already marked the task running
    await reconcile_from_job(runtime_of(memo), name, body)
