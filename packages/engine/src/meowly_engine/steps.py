"""What each kind of task does. A step receives the resolved spec and returns the outputs."""

from collections.abc import Callable, Mapping

from meowly_contracts import TaskEventType, TaskKind, TaskSpec, UnavailableError
from meowly_engine.events import Emit

type Step = Callable[[TaskSpec, Emit], Mapping[str, str]]


def noop(spec: TaskSpec, emit: Emit) -> Mapping[str, str]:
    """Runs nothing and succeeds: enough to exercise API -> CR -> controller -> pod."""
    emit(TaskEventType.STEP, "noop", {})
    return {}


def scaffold(spec: TaskSpec, emit: Emit) -> Mapping[str, str]:
    # The shape exists so the wiring is real; the behaviour does not, and pretending would
    # report a repository that was never created.
    raise UnavailableError("scaffold tasks are not implemented yet")


def provision(spec: TaskSpec, emit: Emit) -> Mapping[str, str]:
    raise UnavailableError("provision tasks are not implemented yet")


# A plain dict (not frozen) so tests can swap a step in; production code never mutates it.
STEPS: dict[TaskKind, Step] = {
    TaskKind.NOOP: noop,
    TaskKind.SCAFFOLD: scaffold,
    TaskKind.PROVISION: provision,
}
