"""The `PlatformTask` custom resource: the execution itself (ADR 0002).

The API creates one per request, the controller reconciles it into a Job and writes its
status back, and the UI reads it. Nothing about an execution lives in Postgres.
"""

from collections.abc import Mapping
from typing import Any, Final

from meowly_contracts._base import Model
from meowly_contracts.task import TaskSpec, TaskStatus

GROUP: Final = "meowly.dev"
VERSION: Final = "v1alpha1"
KIND: Final = "PlatformTask"
PLURAL: Final = "platformtasks"
API_VERSION: Final = f"{GROUP}/{VERSION}"

type JsonDict = dict[str, Any]


class PlatformTask(Model):
    """A CR as the rest of the code wants it: identity, spec and status, nothing else."""

    name: str
    namespace: str
    # metadata.uid, present on every object the API server has accepted (so: absent only on a
    # body meowly itself just built). The controller needs it for the Job's ownerReference.
    uid: str | None = None
    spec: TaskSpec
    status: TaskStatus | None = None

    @property
    def phase_or_pending(self) -> TaskStatus:
        """The status, or a pending one when the controller has not written any yet."""
        return self.status or TaskStatus()


def task_body(
    name: str,
    *,
    namespace: str,
    spec: TaskSpec,
    labels: Mapping[str, str] | None = None,
) -> JsonDict:
    """The CR body to POST to the Kubernetes API."""
    metadata: JsonDict = {"name": name, "namespace": namespace}
    if labels:
        metadata["labels"] = dict(labels)
    return {
        "apiVersion": API_VERSION,
        "kind": KIND,
        "metadata": metadata,
        "spec": spec.model_dump(mode="json"),
    }


def task_from_body(body: Mapping[str, Any]) -> PlatformTask:
    """A CR body (the Kubernetes API's answer, or the one kopf hands a handler) parsed.

    Raises `pydantic.ValidationError` when the object is not a PlatformTask this version
    understands; callers treat that as a malformed resource, never as a transient failure.
    """
    metadata: Mapping[str, Any] = body.get("metadata") or {}
    status: Mapping[str, Any] | None = body.get("status") or None
    return PlatformTask.model_validate(
        {
            "name": metadata.get("name"),
            "namespace": metadata.get("namespace"),
            "uid": metadata.get("uid"),
            "spec": body.get("spec") or {},
            "status": status,
        }
    )
