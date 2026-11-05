"""The Job that runs one PlatformTask."""

from typing import Final

from purr_contracts import (
    API_VERSION,
    COMPONENT_LABEL,
    KIND,
    MANAGED_BY,
    MANAGED_BY_LABEL,
    TASK_LABEL,
    JsonDict,
    PlatformTask,
)
from purr_contracts import ValidationError as InvalidTask
from purr_controller.settings import Settings

WORKER_CONTAINER: Final = "worker"
# Matches `useradd --uid 10001` in the worker Dockerfile and the chart's runAsUser.
WORKER_UID: Final = 10001


def job_manifest(task: PlatformTask, cfg: Settings) -> JsonDict:
    """The Job for `task`. Its name is the task's, so creating it twice is idempotent.

    The ownerReference is what makes deleting the task (the TTL prune) delete the Job and its
    pod too, and Kubernetes rejects one without a uid. A task read from the API server always
    has one, so a missing uid means a body purr built itself: refuse to make an orphan Job.
    """
    if task.uid is None:
        raise InvalidTask(f"PlatformTask {task.name} has no uid: its Job would be an orphan")
    labels = {TASK_LABEL: task.name, MANAGED_BY_LABEL: MANAGED_BY}
    if task.spec.component:
        labels[COMPONENT_LABEL] = task.spec.component
    container: JsonDict = {
        "name": WORKER_CONTAINER,
        "image": cfg.worker_image,
        "imagePullPolicy": cfg.worker_image_pull_policy,
        "env": [
            {"name": "PURR_TASK_NAME", "value": task.name},
            {"name": "PURR_TASK_SPEC", "value": task.spec.model_dump_json()},
        ],
        "securityContext": {
            "allowPrivilegeEscalation": False,
            "readOnlyRootFilesystem": True,
            "capabilities": {"drop": ["ALL"]},
        },
    }
    if cfg.worker_resources:
        container["resources"] = cfg.worker_resources
    return {
        "apiVersion": "batch/v1",
        "kind": "Job",
        "metadata": {
            "name": task.name,
            "namespace": cfg.execution_namespace,
            "labels": labels,
            "ownerReferences": [
                {
                    "apiVersion": API_VERSION,
                    "kind": KIND,
                    "name": task.name,
                    "uid": task.uid,
                    "controller": True,
                }
            ],
        },
        "spec": {
            "backoffLimit": cfg.job_backoff_limit,
            "activeDeadlineSeconds": cfg.job_active_deadline_seconds,
            "template": {
                "metadata": {"labels": labels},
                "spec": {
                    "restartPolicy": "Never",
                    "serviceAccountName": cfg.worker_service_account,
                    # The worker talks to no API server (ADR 0002): do not hand it a token.
                    "automountServiceAccountToken": False,
                    "securityContext": {
                        "runAsNonRoot": True,
                        "runAsUser": WORKER_UID,
                        "runAsGroup": WORKER_UID,
                        "seccompProfile": {"type": "RuntimeDefault"},
                    },
                    "containers": [container],
                },
            },
        },
    }
