import io
from importlib.metadata import entry_points

from purr_contracts import (
    TaskEventType,
    TaskKind,
    TaskPhase,
    TaskSpec,
    ValidationError,
    decode_event,
    status_from_event,
)
from purr_worker.pod import run_task
from purr_worker.settings import Settings


def _settings(spec: str) -> Settings:
    return Settings(task_name="task-1", task_spec=spec)


def test_valid_spec_exits_zero_and_prints_jsonl_events() -> None:
    spec = TaskSpec(kind=TaskKind.NOOP, requested_by="daniel")
    out = io.StringIO()

    code = run_task(_settings(spec.model_dump_json()), stdout=out)

    assert code == 0
    events = [decode_event(line) for line in out.getvalue().splitlines()]
    assert all(e is not None for e in events)
    assert [e.type for e in events if e is not None] == [
        TaskEventType.STARTED,
        TaskEventType.STEP,
        TaskEventType.FINISHED,
    ]


def test_failed_task_exits_one() -> None:
    spec = TaskSpec(kind=TaskKind.SCAFFOLD, requested_by="daniel")
    assert run_task(_settings(spec.model_dump_json()), stdout=io.StringIO()) == 1


def test_malformed_spec_exits_one_with_a_failed_finished_event() -> None:
    out = io.StringIO()

    code = run_task(_settings('{"kind": "nope"}'), stdout=out)

    assert code == 1
    lines = out.getvalue().splitlines()
    assert len(lines) == 1
    event = decode_event(lines[0])
    assert event is not None
    assert event.type is TaskEventType.FINISHED
    status = status_from_event(event)
    assert status is not None
    assert status.phase is TaskPhase.FAILED
    assert status.error == ValidationError.code


def test_console_script_resolves_to_main_run() -> None:
    (script,) = [ep for ep in entry_points(group="console_scripts") if ep.name == "purr-worker"]
    assert script.value == "purr_worker.main:run"
    assert callable(script.load())
