"""Job events: when a purr Job ends, its task gets the final status."""

from collections.abc import Mapping
from typing import Any

import kopf
import structlog

from purr_contracts import TASK_LABEL
from purr_controller.handlers.runtime import runtime_of
from purr_controller.services.reconcile import JobOutcome, job_state, next_status

log = structlog.get_logger(__name__)


async def job_event(
    body: Mapping[str, Any], event: Mapping[str, Any], memo: kopf.Memo, **_: object
) -> None:
    if event.get("type") == "DELETED":
        return
    labels: Mapping[str, str] = body.get("metadata", {}).get("labels") or {}
    name = labels[TASK_LABEL]
    state = job_state(body)
    if state.outcome is JobOutcome.ACTIVE:
        return  # the create handler already marked the task running

    rt = runtime_of(memo)
    task = await rt.kube.get_task(name)
    if task is None:
        return
    # The log is only read once the Job has ended: the final result is in it.
    log_text = await rt.kube.pod_log(name)
    status = next_status(task.status, state, log_text)
    if status is not None:
        await rt.kube.patch_task_status(name, status)
        log.info("task.finished", task=name, phase=status.phase.value)
