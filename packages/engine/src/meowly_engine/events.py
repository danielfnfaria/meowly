"""Writing the task's event stream (JSONL on stdout, ADR 0002)."""

import sys
from collections.abc import Mapping
from typing import Protocol, TextIO

from meowly_contracts import TaskEvent, TaskEventType, encode_event


class Emit(Protocol):
    """What a step is given to report progress: it never sees the writer behind it, so a step
    cannot write anything to the stream except well-formed events."""

    def __call__(self, type: TaskEventType, message: str, data: Mapping[str, str], /) -> None: ...


class EventWriter:
    """Numbers events (`seq` starts at 1, never repeats) and writes one JSON line each.

    The stream is flushed per event: the controller reads the pod log after the process exits,
    but a person tailing `kubectl logs` of a long task should see progress as it happens.
    """

    def __init__(self, stream: TextIO | None = None) -> None:
        # Resolved at call time, not at import time, so a captured/replaced sys.stdout is honoured.
        self._stream = stream
        self._seq = 0

    @property
    def seq(self) -> int:
        """Sequence number of the last event written (0 before the first)."""
        return self._seq

    def emit(self, type: TaskEventType, message: str, data: Mapping[str, str], /) -> None:
        self._seq += 1
        event = TaskEvent(seq=self._seq, type=type, message=message, data=dict(data))
        stream = self._stream if self._stream is not None else sys.stdout
        stream.write(encode_event(event) + "\n")
        stream.flush()
