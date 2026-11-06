from enum import StrEnum


class TaskKind(StrEnum):
    """What a task does. `noop` exists for the walking skeleton and the tests: it runs
    nothing and succeeds, which is enough to exercise API -> CR -> controller -> pod."""

    NOOP = "noop"
    SCAFFOLD = "scaffold"
    PROVISION = "provision"


class TaskPhase(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"

    @property
    def terminal(self) -> bool:
        """A terminal phase is never left: the controller stops reconciling and the TTL starts."""
        return self in _TERMINAL


_TERMINAL = frozenset({TaskPhase.SUCCEEDED, TaskPhase.FAILED, TaskPhase.CANCELLED})
