from purr_contracts import (
    API_VERSION,
    KIND,
    TaskKind,
    TaskPhase,
    TaskSpec,
    task_body,
    task_from_body,
)


def _spec() -> TaskSpec:
    return TaskSpec(kind=TaskKind.NOOP, component="checkout", requested_by="daniel")


def test_body_is_a_platformtask_the_api_can_post() -> None:
    body = task_body("task-1", namespace="purr", spec=_spec(), labels={"purr.sh/task": "task-1"})
    assert body["apiVersion"] == API_VERSION
    assert body["kind"] == KIND
    assert body["metadata"] == {
        "name": "task-1",
        "namespace": "purr",
        "labels": {"purr.sh/task": "task-1"},
    }
    assert body["spec"]["kind"] == "noop"


def test_a_body_without_status_reads_back_as_pending() -> None:
    task = task_from_body(task_body("task-1", namespace="purr", spec=_spec()))
    assert task.name == "task-1"
    assert task.namespace == "purr"
    assert task.status is None
    assert task.phase_or_pending.phase is TaskPhase.PENDING


def test_the_status_written_by_the_controller_reads_back() -> None:
    body = task_body("task-1", namespace="purr", spec=_spec())
    body["status"] = {"phase": "succeeded", "outputs": {"url": "https://example.test"}}
    task = task_from_body(body)
    assert task.status is not None
    assert task.status.phase is TaskPhase.SUCCEEDED
    assert task.status.outputs == {"url": "https://example.test"}
