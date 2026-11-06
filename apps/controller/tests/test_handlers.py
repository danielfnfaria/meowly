import json
from collections.abc import Mapping
from typing import Any

import kopf

from meowly_contracts import (
    COMPONENT_LABEL,
    MANAGED_BY,
    MANAGED_BY_LABEL,
    TASK_LABEL,
    TaskEvent,
    TaskEventType,
    TaskKind,
    TaskPhase,
    TaskSpec,
    TaskStatus,
    encode_event,
)
from meowly_controller.adapters.memory import MemoryKube
from meowly_controller.handlers import job_event, runtime_of, task_created, task_timer
from meowly_controller.settings import Settings

from .conftest import UID, WORKER_IMAGE, finished_status, make_body, old, stored


def _finished_line(status: TaskStatus) -> str:
    event = TaskEvent(seq=3, type=TaskEventType.FINISHED, data={"status": status.model_dump_json()})
    return encode_event(event)


def _job(name: str, **status: Any) -> dict[str, Any]:
    return {
        "metadata": {
            "name": name,
            "labels": {TASK_LABEL: name, MANAGED_BY_LABEL: MANAGED_BY},
        },
        "status": status,
    }


async def _created(body: Mapping[str, Any], memo: kopf.Memo) -> None:
    await task_created(body=body, name=body["metadata"]["name"], memo=memo)


async def test_create_makes_the_job_and_marks_the_task_running(
    kube: MemoryKube, memo: kopf.Memo, settings: Settings
) -> None:
    body = make_body()
    stored(kube, body)

    await _created(body, memo)

    job = kube.jobs["task-1"]
    pod = job["spec"]["template"]["spec"]
    container = pod["containers"][0]
    env = {e["name"]: e["value"] for e in container["env"]}
    assert container["image"] == WORKER_IMAGE
    assert env["MEOWLY_TASK_NAME"] == "task-1"
    spec = TaskSpec.model_validate_json(env["MEOWLY_TASK_SPEC"])
    assert spec.kind is TaskKind.NOOP
    assert spec.component == "checkout"
    assert json.loads(env["MEOWLY_TASK_SPEC"])["requested_by"] == "daniel"
    assert pod["serviceAccountName"] == "meowly-worker-sa"
    assert pod["restartPolicy"] == "Never"
    assert pod["securityContext"]["runAsNonRoot"] is True
    assert job["spec"]["backoffLimit"] == 2
    assert job["spec"]["activeDeadlineSeconds"] == 300
    (owner,) = job["metadata"]["ownerReferences"]
    assert (owner["kind"], owner["name"], owner["uid"]) == ("PlatformTask", "task-1", UID)
    labels = job["metadata"]["labels"]
    assert labels[TASK_LABEL] == "task-1"
    assert labels[COMPONENT_LABEL] == "checkout"
    assert labels[MANAGED_BY_LABEL] == MANAGED_BY
    assert job["metadata"]["namespace"] == settings.execution_namespace

    ((name, status),) = kube.status_patches
    assert name == "task-1"
    assert status.phase is TaskPhase.RUNNING
    assert status.started_at is not None


async def test_component_label_is_absent_without_a_component(
    kube: MemoryKube, memo: kopf.Memo
) -> None:
    body = make_body(component=None)
    stored(kube, body)
    await _created(body, memo)
    assert COMPONENT_LABEL not in kube.jobs["task-1"]["metadata"]["labels"]


async def test_resume_of_a_running_task_does_not_rewrite_its_status(
    kube: MemoryKube, memo: kopf.Memo
) -> None:
    body = make_body(status=TaskStatus(phase=TaskPhase.RUNNING))
    stored(kube, body)
    await _created(body, memo)
    assert "task-1" in kube.jobs
    assert kube.status_patches == []


async def test_create_of_a_terminal_task_does_nothing(kube: MemoryKube, memo: kopf.Memo) -> None:
    body = make_body(status=finished_status())
    stored(kube, body)
    await _created(body, memo)
    assert kube.jobs == {}
    assert kube.status_patches == []


async def test_invalid_spec_fails_the_task_without_a_job(kube: MemoryKube, memo: kopf.Memo) -> None:
    body = make_body()
    body["spec"]["kind"] = "bogus"
    await _created(body, memo)
    assert kube.jobs == {}
    ((_, status),) = kube.status_patches
    assert status.phase is TaskPhase.FAILED
    assert status.error == "validation_error"
    # Never ran: without finished_at the TTL prune would never expire it.
    assert status.started_at is not None
    assert status.finished_at == status.started_at


async def test_resume_after_the_job_already_finished_writes_the_final_status(
    kube: MemoryKube, memo: kopf.Memo
) -> None:
    # The controller died after creating the Job: on resume the Job is done, and no further
    # Job event will come. The create handler must not write a blind `running`.
    body = make_body()
    stored(kube, body)
    kube.jobs["task-1"] = _job("task-1", succeeded=1)
    kube.logs["task-1"] = _finished_line(finished_status(outputs={"a": "1"}))

    await _created(body, memo)

    ((_, status),) = kube.status_patches
    assert status.phase is TaskPhase.SUCCEEDED
    assert status.outputs == {"a": "1"}


async def test_resume_after_the_job_failed_without_events_fails_the_task(
    kube: MemoryKube, memo: kopf.Memo
) -> None:
    body = make_body()
    stored(kube, body)
    kube.jobs["task-1"] = _job("task-1", conditions=[{"type": "Failed", "status": "True"}])

    await _created(body, memo)

    ((_, status),) = kube.status_patches
    assert (status.phase, status.error) == (TaskPhase.FAILED, "no_result")
    assert status.finished_at is not None


async def test_succeeded_job_writes_the_reported_status(kube: MemoryKube, memo: kopf.Memo) -> None:
    stored(kube, make_body(status=TaskStatus(phase=TaskPhase.RUNNING)))
    reported = finished_status(outputs={"url": "https://example.test/repo"})
    kube.logs["task-1"] = "\n".join(
        ["not json at all", _finished_line(reported), '{"seq": "garbage"}']
    )

    await job_event(body=_job("task-1", succeeded=1), event={"type": "MODIFIED"}, memo=memo)

    ((_, status),) = kube.status_patches
    assert status.phase is TaskPhase.SUCCEEDED
    assert status.outputs == {"url": "https://example.test/repo"}


async def test_failed_job_without_events_fails_with_a_no_report_message(
    kube: MemoryKube, memo: kopf.Memo
) -> None:
    stored(kube, make_body(status=TaskStatus(phase=TaskPhase.RUNNING)))
    kube.logs["task-1"] = "Traceback (most recent call last): ..."
    job = _job("task-1", failed=1, conditions=[{"type": "Failed", "status": "True"}])

    await job_event(body=job, event={"type": "MODIFIED"}, memo=memo)

    ((_, status),) = kube.status_patches
    assert status.phase is TaskPhase.FAILED
    assert status.message is not None
    assert "did not report" in status.message
    assert status.finished_at is not None


async def test_failed_job_keeps_the_error_the_worker_reported(
    kube: MemoryKube, memo: kopf.Memo
) -> None:
    stored(kube, make_body(status=TaskStatus(phase=TaskPhase.RUNNING)))
    reported = finished_status(TaskPhase.FAILED, error="unavailable", message="not implemented")
    kube.logs["task-1"] = _finished_line(reported)
    job = _job("task-1", conditions=[{"type": "Failed", "status": "True"}])

    await job_event(body=job, event={"type": "MODIFIED"}, memo=memo)

    ((_, status),) = kube.status_patches
    assert (status.phase, status.error) == (TaskPhase.FAILED, "unavailable")


async def test_active_job_event_writes_nothing(kube: MemoryKube, memo: kopf.Memo) -> None:
    stored(kube, make_body(status=TaskStatus(phase=TaskPhase.RUNNING)))
    await job_event(body=_job("task-1", active=1), event={"type": "MODIFIED"}, memo=memo)
    assert kube.status_patches == []


async def test_terminal_task_is_never_rewritten_by_a_late_job_event(
    kube: MemoryKube, memo: kopf.Memo
) -> None:
    stored(kube, make_body(status=finished_status(outputs={"a": "1"})))
    kube.logs["task-1"] = _finished_line(finished_status(TaskPhase.FAILED, error="x"))

    await job_event(body=_job("task-1", succeeded=1), event={"type": "MODIFIED"}, memo=memo)

    assert kube.status_patches == []


async def test_job_event_for_a_deleted_job_or_unknown_task_is_ignored(
    kube: MemoryKube, memo: kopf.Memo
) -> None:
    await job_event(body=_job("ghost", succeeded=1), event={"type": "DELETED"}, memo=memo)
    await job_event(body=_job("ghost", succeeded=1), event={"type": "ADDED"}, memo=memo)
    assert kube.status_patches == []


async def _prune(kube: MemoryKube, memo: kopf.Memo, name: str) -> None:
    task = kube.tasks[name]
    body = make_body(name, status=task.status)
    await task_timer(body=body, name=name, memo=memo)


async def test_timer_reconciles_a_running_task_whose_job_already_ended(
    kube: MemoryKube, memo: kopf.Memo
) -> None:
    stored(kube, make_body(status=TaskStatus(phase=TaskPhase.RUNNING, started_at=old(60))))
    kube.jobs["task-1"] = _job("task-1", succeeded=1)
    kube.logs["task-1"] = _finished_line(finished_status(outputs={"a": "1"}))

    await _prune(kube, memo, "task-1")

    ((_, status),) = kube.status_patches
    assert status.phase is TaskPhase.SUCCEEDED
    assert kube.deleted_tasks == []


async def test_timer_fails_a_running_task_whose_job_is_gone(
    kube: MemoryKube, memo: kopf.Memo
) -> None:
    started = old(60)
    stored(kube, make_body(status=TaskStatus(phase=TaskPhase.RUNNING, started_at=started)))

    await _prune(kube, memo, "task-1")

    ((_, status),) = kube.status_patches
    assert (status.phase, status.error) == (TaskPhase.FAILED, "job_missing")
    assert status.started_at == started
    assert status.finished_at is not None


async def test_timer_leaves_alone_a_pending_task_without_a_job_and_an_active_job(
    kube: MemoryKube, memo: kopf.Memo
) -> None:
    # Pending: the create handler has not made the Job yet; failing it would race that.
    stored(kube, make_body("pending"))
    stored(kube, make_body("active", status=TaskStatus(phase=TaskPhase.RUNNING)))
    kube.jobs["active"] = _job("active", active=1)

    await _prune(kube, memo, "pending")
    await _prune(kube, memo, "active")

    assert kube.status_patches == []


async def test_ttl_prune_deletes_only_terminal_and_old_tasks(
    kube: MemoryKube, memo: kopf.Memo
) -> None:
    ttl = 600  # settings fixture
    done_old = finished_status().model_copy(update={"finished_at": old(ttl + 5)})
    done_recent = finished_status().model_copy(update={"finished_at": old(ttl - 300)})
    running_old = TaskStatus(phase=TaskPhase.RUNNING, started_at=old(ttl * 10))
    for name, status in [
        ("old-done", done_old),
        ("recent-done", done_recent),
        ("old-running", running_old),
        ("fresh-pending", None),
    ]:
        stored(kube, make_body(name, status=status))

    for name in list(kube.tasks):
        await _prune(kube, memo, name)

    assert kube.deleted_tasks == ["old-done"]


async def test_the_job_carries_resources_and_pull_policy_from_settings(
    kube: MemoryKube, memo: kopf.Memo, settings: Settings
) -> None:
    resources = {"requests": {"cpu": "50m"}, "limits": {"memory": "256Mi"}}
    rt = runtime_of(memo)
    configured = settings.model_copy(
        update={"worker_resources": resources, "worker_image_pull_policy": "Always"}
    )
    memo["runtime"] = type(rt)(settings=configured, kube=kube)
    body = make_body()
    stored(kube, body)

    await _created(body, memo)

    container = kube.jobs["task-1"]["spec"]["template"]["spec"]["containers"][0]
    assert container["resources"] == resources
    assert container["imagePullPolicy"] == "Always"


async def test_the_job_has_no_resources_key_when_none_are_configured(
    kube: MemoryKube, memo: kopf.Memo
) -> None:
    body = make_body()
    stored(kube, body)
    await _created(body, memo)
    assert "resources" not in kube.jobs["task-1"]["spec"]["template"]["spec"]["containers"][0]
