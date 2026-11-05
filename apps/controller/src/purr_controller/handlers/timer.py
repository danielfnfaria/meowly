"""TTL pruning of finished tasks."""

from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any

import kopf
import structlog

from purr_contracts import task_from_body
from purr_controller.handlers.runtime import runtime_of
from purr_controller.services.reconcile import expired

log = structlog.get_logger(__name__)

PRUNE_INTERVAL_SECONDS = 60.0


async def task_timer(body: Mapping[str, Any], name: str, memo: kopf.Memo, **_: object) -> None:
    """Delete a terminal task older than the TTL. The Job and its pod go with it through the
    ownerReference, so this is the only cleanup there is."""
    rt = runtime_of(memo)
    try:
        task = task_from_body(body)
    except ValueError:
        return  # not a task this version reads; leave it for a human
    if expired(task.status, rt.settings.task_ttl_seconds, now=datetime.now(UTC)):
        await rt.kube.delete_task(name)
        log.info("task.pruned", task=name)
