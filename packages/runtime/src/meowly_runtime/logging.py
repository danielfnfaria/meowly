import logging
import sys
from typing import Literal

import structlog

DEFAULT_QUIET_LOGGERS: tuple[str, ...] = ("uvicorn.access", "httpx", "httpcore")
"""Loggers held at WARNING unless the process passes its own list."""


def configure_logging(
    level: str,
    *,
    stream: Literal["stdout", "stderr"] = "stdout",
    quiet: tuple[str, ...] = DEFAULT_QUIET_LOGGERS,
) -> None:
    """JSON logs on `stream`; stdlib loggers (uvicorn, sqlalchemy, kopf...) are routed through
    structlog and the `quiet` ones are held at WARNING.

    The worker passes `stream="stderr"`: its stdout is the task's event stream (JSONL) and
    carries nothing else.
    """
    shared: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]
    structlog.configure(
        processors=[*shared, structlog.stdlib.ProcessorFormatter.wrap_for_formatter],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.processors.JSONRenderer(),
        ],
    )
    handler = logging.StreamHandler(sys.stderr if stream == "stderr" else sys.stdout)
    handler.setFormatter(formatter)
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level.upper())
    for noisy in quiet:
        logging.getLogger(noisy).setLevel(logging.WARNING)
