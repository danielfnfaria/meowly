"""A terminal status without `finished_at` is never pruned (`expired` needs it), so the task
would stay in the cluster forever and wake the timer every minute.

This drives every controller path that writes a status and asserts none of them lets a
terminal one out without it.
"""

from contextlib import suppress
from datetime import UTC, datetime

import kopf
import pytest

from purr_contracts import (
    MANAGED_BY,
    MANAGED_BY_LABEL,
    TASK_LABEL,
    JsonDict,
    TaskEvent,
    TaskEventType,
    TaskKind,
    TaskPhase,
    TaskSpec,
    TaskStatus,
    encode_event,
    task_body,
    task_from_body,
)
from purr_controller.adapters.memory import MemoryKube
from purr_controller.handlers import Runtime, job_event, task_created, task_timer
from purr_controller.settings import Settings

NAME = "task-1"


def _body(*, status: TaskStatus | None = None, kind: str = "noop") -> JsonDict:
    spec = TaskSpec(kind=TaskKind.NOOP, requested_by="tester")
    body = task_body(NAME, namespace="purr", spec=spec)
    body["metadata"]["uid"] = "7b6c1d2e-0000-0000-0000-000000000001"
    body["spec"]["kind"] = kind
    if status is not None:
        body["status"] = status.model_dump(mode="json")
    return body


def _job(**status: object) -> JsonDict:
    labels = {TASK_LABEL: NAME, MANAGED_BY_LABEL: MANAGED_BY}
    return {"metadata": {"name": NAME, "labels": labels}, "status": status}


def _finished(status: TaskStatus) -> str:
    # What a worker prints: the engine's own timestamps may well be absent.
    event = TaskEvent(seq=1, type=TaskEventType.FINISHED, data={"status": status.model_dump_json()})
    return encode_event(event)


FAILED_COND = {"conditions": [{"type": "Failed", "status": "True"}]}
RUNNING = TaskStatus(phase=TaskPhase.RUNNING, started_at=datetime.now(UTC))
SUCCEEDED_NO_TIMES = TaskStatus(phase=TaskPhase.SUCCEEDED)
FAILED_NO_TIMES = TaskStatus(phase=TaskPhase.FAILED, error="x")

# name -> (task body, job in the cluster or None, pod log, handler)
CASES = {
    "invalid spec": (_body(kind="bogus"), None, "", "created"),
    "resume, job done, result reported": (
        _body(),
        _job(succeeded=1),
        _finished(SUCCEEDED_NO_TIMES),
        "created",
    ),
    "resume, job failed, nothing reported": (_body(), _job(**FAILED_COND), "", "created"),
    "job event, success without timestamps": (
        _body(status=RUNNING),
        _job(succeeded=1),
        _finished(SUCCEEDED_NO_TIMES),
        "job",
    ),
    "job event, failure without timestamps": (
        _body(status=RUNNING),
        _job(**FAILED_COND),
        _finished(FAILED_NO_TIMES),
        "job",
    ),
    "job event, succeeded but no log": (_body(status=RUNNING), _job(succeeded=1), "", "job"),
    "timer, job ended": (_body(status=RUNNING), _job(succeeded=1), "", "timer"),
    "timer, job gone": (_body(status=RUNNING), None, "", "timer"),
}


@pytest.mark.parametrize("case", CASES)
async def test_no_terminal_status_leaves_the_controller_without_finished_at(case: str) -> None:
    body, job, log, handler = CASES[case]
    kube = MemoryKube()
    memo = kopf.Memo()
    memo["runtime"] = Runtime(settings=Settings(worker_image="img"), kube=kube)
    # The invalid-spec case: the API server holds it, purr cannot parse it.
    with suppress(ValueError):
        kube.tasks[NAME] = task_from_body(body)
    if job is not None:
        kube.jobs[NAME] = job
    kube.logs[NAME] = log

    if handler == "created":
        await task_created(body=body, name=NAME, memo=memo)
    elif handler == "job":
        assert job is not None
        await job_event(body=job, event={"type": "MODIFIED"}, memo=memo)
    else:
        await task_timer(body=body, name=NAME, memo=memo)

    terminal = [status for _, status in kube.status_patches if status.terminal]
    assert terminal, "the case was expected to write a terminal status"
    for status in terminal:
        assert status.finished_at is not None
