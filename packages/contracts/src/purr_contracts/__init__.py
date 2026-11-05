"""The wire of purr: task spec, status and events, the PlatformTask envelope and the errors.

This package imports no other workspace package (import-linter keeps it that way).
"""

from purr_contracts._base import Model
from purr_contracts.enums import TaskKind, TaskPhase
from purr_contracts.errors import (
    AuthenticationError,
    ConflictError,
    NotFoundError,
    PayloadTooLargeError,
    PermissionDeniedError,
    PurrError,
    UnavailableError,
    UpstreamError,
    ValidationError,
)
from purr_contracts.events import (
    TaskEvent,
    TaskEventType,
    decode_event,
    encode_event,
    finished_data,
    status_from_event,
)
from purr_contracts.labels import (
    COMPONENT_LABEL,
    MANAGED_BY,
    MANAGED_BY_LABEL,
    TASK_LABEL,
)
from purr_contracts.platformtask import (
    API_VERSION,
    GROUP,
    KIND,
    PLURAL,
    VERSION,
    JsonDict,
    PlatformTask,
    task_body,
    task_from_body,
)
from purr_contracts.task import TaskSpec, TaskStatus
from purr_contracts.version import SPEC_VERSION

__all__ = [
    "API_VERSION",
    "COMPONENT_LABEL",
    "GROUP",
    "KIND",
    "MANAGED_BY",
    "MANAGED_BY_LABEL",
    "PLURAL",
    "SPEC_VERSION",
    "TASK_LABEL",
    "VERSION",
    "AuthenticationError",
    "ConflictError",
    "JsonDict",
    "Model",
    "NotFoundError",
    "PayloadTooLargeError",
    "PermissionDeniedError",
    "PlatformTask",
    "PurrError",
    "TaskEvent",
    "TaskEventType",
    "TaskKind",
    "TaskPhase",
    "TaskSpec",
    "TaskStatus",
    "UnavailableError",
    "UpstreamError",
    "ValidationError",
    "decode_event",
    "encode_event",
    "finished_data",
    "status_from_event",
    "task_body",
    "task_from_body",
]
