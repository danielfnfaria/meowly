import json
import logging

import pytest
import structlog

from purr_runtime import configure_logging


def test_logs_come_out_as_one_json_object_per_line(capsys: pytest.CaptureFixture[str]) -> None:
    configure_logging("INFO")
    structlog.get_logger("test").info("task.started", task="task-1")
    payload = json.loads(capsys.readouterr().out.strip())
    assert payload["event"] == "task.started"
    assert payload["task"] == "task-1"
    assert payload["level"] == "info"


def test_the_worker_can_keep_its_stdout_clean(capsys: pytest.CaptureFixture[str]) -> None:
    # The pod's stdout is the task's event stream: the worker's own logs go to stderr.
    configure_logging("INFO", stream="stderr")
    structlog.get_logger("test").info("worker.started")
    captured = capsys.readouterr()
    assert captured.out == ""
    assert json.loads(captured.err.strip())["event"] == "worker.started"


def test_noisy_loggers_are_held_at_warning() -> None:
    configure_logging("DEBUG")
    assert logging.getLogger("uvicorn.access").level == logging.WARNING
    assert logging.getLogger().level == logging.DEBUG
