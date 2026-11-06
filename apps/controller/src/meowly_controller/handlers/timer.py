"""TTL pruning of finished tasks, and convergence of the ones a watcher missed."""

from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any

import kopf
import structlog

from meowly_contracts import TaskPhase, TaskStatus, task_from_body
from meowly_controller.handlers.job import reconcile_from_job
from meowly_controller.handlers.runtime import Runtime, runtime_of
from meowly_controller.services.reconcile import expired, lost_job_status

log = structlog.get_logger(__name__)

PRUNE_INTERVAL_SECONDS = 60.0


async def task_timer(body: Mapping[str, Any], name: str, memo: kopf.Memo, **_: object) -> None:
    """Delete a terminal task older than the TTL (the Job and its pod go with it through the
    ownerReference, so this is the only cleanup there is) and converge a non-terminal one."""
    rt = runtime_of(memo)
    try:
        task = task_from_body(body)
    except ValueError:
        return  # not a task this version reads; leave it for a human
    if expired(task.status, rt.settings.task_ttl_seconds, now=datetime.now(UTC)):
        await rt.kube.delete_task(name)
        log.info("task.pruned", task=name)
        return
    if task.status is not None and task.status.terminal:
        return
    await _converge(rt, name, task.status)


async def _converge(rt: Runtime, name: str, status: TaskStatus | None) -> None:
    """Safety net for what a watcher missed: a task that is not terminal but whose Job has
    ended (the Job event was lost or handled before the task had a status), or whose Job is
    gone. Without it such a task would stay non-terminal, and never be pruned, forever."""
    job = await rt.kube.get_job(name)
    if job is not None:
        await reconcile_from_job(rt, name, job)
        return
    # Only a task already `running` had its Job created: a pending one is still waiting for
    # the create handler, and failing it here would race that handler.
    if status is None or status.phase is not TaskPhase.RUNNING:
        return
    # The body kopf hands over can be stale: re-read before writing a terminal status.
    fresh = await rt.kube.get_task(name)
    if fresh is None or (fresh.status is not None and fresh.status.terminal):
        return
    await rt.kube.patch_task_status(name, lost_job_status(fresh.status))
    log.warning("task.job_missing", task=name)
