from purr_contracts import TaskEvent, TaskEventType, decode_event, encode_event


def test_an_event_survives_a_round_trip() -> None:
    event = TaskEvent(seq=1, type=TaskEventType.STEP, message="render", data={"step": "noop"})
    decoded = decode_event(encode_event(event))
    assert decoded is not None
    assert decoded.seq == 1
    assert decoded.type is TaskEventType.STEP
    assert decoded.data == {"step": "noop"}


def test_a_line_that_is_not_an_event_is_skipped() -> None:
    # Anything a dependency prints to the pod's stdout: a reader skips it, never fails.
    assert decode_event("") is None
    assert decode_event("Downloading something...") is None
    assert decode_event("[1, 2, 3]") is None
    assert decode_event('{"seq": 0, "type": "step"}') is None
