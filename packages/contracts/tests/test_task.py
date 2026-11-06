import pytest
from pydantic import ValidationError as PydanticValidationError

from meowly_contracts import SPEC_VERSION, TaskKind, TaskPhase, TaskSpec, TaskStatus


def test_spec_carries_the_current_wire_version() -> None:
    spec = TaskSpec(kind=TaskKind.NOOP, requested_by="daniel")
    assert spec.spec_version == SPEC_VERSION
    assert spec.inputs == {}


def test_an_unknown_field_is_refused() -> None:
    with pytest.raises(PydanticValidationError):
        TaskSpec.model_validate({"kind": "noop", "requested_by": "daniel", "typo": 1})


def test_a_fresh_status_is_pending_and_not_terminal() -> None:
    status = TaskStatus()
    assert status.phase is TaskPhase.PENDING
    assert not status.terminal


@pytest.mark.parametrize(
    ("phase", "terminal"),
    [
        (TaskPhase.PENDING, False),
        (TaskPhase.RUNNING, False),
        (TaskPhase.SUCCEEDED, True),
        (TaskPhase.FAILED, True),
        (TaskPhase.CANCELLED, True),
    ],
)
def test_terminal_phases(phase: TaskPhase, terminal: bool) -> None:
    assert phase.terminal is terminal
