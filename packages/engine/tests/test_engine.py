import io

import pytest

from purr_contracts import (
    TaskEvent,
    TaskEventType,
    TaskKind,
    TaskPhase,
    TaskSpec,
    UnavailableError,
    decode_event,
    status_from_event,
)
from purr_engine import STEPS, Emit, EventWriter, execute


def _spec(kind: TaskKind) -> TaskSpec:
    return TaskSpec(kind=kind, requested_by="daniel")


def _events(stream: io.StringIO) -> list[TaskEvent]:
    events = [decode_event(line) for line in stream.getvalue().splitlines()]
    assert None not in events
    return [e for e in events if e is not None]


def test_noop_succeeds_and_emits_started_step_finished() -> None:
    stream = io.StringIO()
    status = execute(_spec(TaskKind.NOOP), writer=EventWriter(stream))

    assert status.phase is TaskPhase.SUCCEEDED
    assert status.outputs == {}
    assert status.started_at is not None
    assert status.finished_at is not None
    assert status.started_at <= status.finished_at
    events = _events(stream)
    assert [e.type for e in events] == [
        TaskEventType.STARTED,
        TaskEventType.STEP,
        TaskEventType.FINISHED,
    ]
    assert [e.seq for e in events] == [1, 2, 3]


def test_every_line_is_a_single_decodable_event() -> None:
    stream = io.StringIO()
    execute(_spec(TaskKind.NOOP), writer=EventWriter(stream))
    lines = stream.getvalue().splitlines()
    assert lines
    assert all(decode_event(line) is not None for line in lines)


def test_finished_event_carries_the_final_status() -> None:
    stream = io.StringIO()
    status = execute(_spec(TaskKind.NOOP), writer=EventWriter(stream))
    finished = _events(stream)[-1]
    reported = status_from_event(finished)
    assert reported is not None
    assert reported.phase is TaskPhase.SUCCEEDED
    assert reported == status


@pytest.mark.parametrize("kind", [TaskKind.SCAFFOLD, TaskKind.PROVISION])
def test_unimplemented_kind_fails_with_the_unavailable_code(kind: TaskKind) -> None:
    status = execute(_spec(kind), writer=EventWriter(io.StringIO()))
    assert status.phase is TaskPhase.FAILED
    assert status.error == UnavailableError.code
    assert status.message is not None
    assert "not implemented" in status.message


def test_unexpected_error_fails_without_leaking_the_stacktrace(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def boom(spec: TaskSpec, emit: Emit) -> dict[str, str]:
        raise ValueError("secret detail /srv/internal/path")

    monkeypatch.setitem(STEPS, TaskKind.NOOP, boom)
    stream = io.StringIO()
    status = execute(_spec(TaskKind.NOOP), writer=EventWriter(stream))

    assert status.phase is TaskPhase.FAILED
    assert status.error == "internal_error"
    assert status.message is not None
    assert "secret" not in status.message
    assert "Traceback" not in stream.getvalue()
    assert "secret" not in stream.getvalue()
    assert _events(stream)[-1].type is TaskEventType.FINISHED
