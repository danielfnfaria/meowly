"""The wire of meowly: task spec, status and events, the PlatformTask envelope and the errors.

This package imports no other workspace package (import-linter keeps it that way).
"""

from meowly_contracts._base import Model
from meowly_contracts.enums import TaskKind, TaskPhase
from meowly_contracts.errors import (
    AuthenticationError,
    ConflictError,
    MeowlyError,
    NotFoundError,
    PayloadTooLargeError,
    PermissionDeniedError,
    UnavailableError,
    UpstreamError,
    ValidationError,
)
from meowly_contracts.events import (
    TaskEvent,
    TaskEventType,
    decode_event,
    encode_event,
    finished_data,
    status_from_event,
)
from meowly_contracts.labels import (
    COMPONENT_LABEL,
    MANAGED_BY,
    MANAGED_BY_LABEL,
    TASK_LABEL,
)
from meowly_contracts.platformtask import (
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
from meowly_contracts.task import TaskSpec, TaskStatus
from meowly_contracts.version import SPEC_VERSION

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
    "MeowlyError",
    "Model",
    "NotFoundError",
    "PayloadTooLargeError",
    "PermissionDeniedError",
    "PlatformTask",
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
