# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnknownArgumentType=false
# lightkube ships partial type information; the calls below are checked by tests instead.
"""`Kube` over lightkube's async client (in-cluster config, or kubeconfig outside)."""

from collections.abc import Generator
from contextlib import contextmanager
from typing import Any, cast

from lightkube import ApiError, AsyncClient
from lightkube.generic_resource import create_namespaced_resource
from lightkube.resources.batch_v1 import Job
from lightkube.resources.core_v1 import Pod
from lightkube.types import CascadeType, PatchType

from purr_contracts import (
    GROUP,
    KIND,
    PLURAL,
    VERSION,
    JsonDict,
    PlatformTask,
    TaskStatus,
    UpstreamError,
    task_from_body,
)
from purr_controller.services.job import WORKER_CONTAINER

FIELD_MANAGER = "purr-controller"

Task = create_namespaced_resource(GROUP, VERSION, KIND, PLURAL)


@contextmanager
def _upstream(*ignore: int) -> Generator[None]:
    """Turn a cluster error into `UpstreamError`, except the status codes in `ignore`
    (409 on create: a retry; 404 on delete: already gone)."""
    try:
        yield
    except ApiError as exc:
        if exc.status.code in ignore:
            return
        raise UpstreamError(
            f"kubernetes answered {exc.status.code}: {exc.status.message or exc.status.reason}"
        ) from exc


class LightkubeKube:
    def __init__(self, client: AsyncClient, namespace: str) -> None:
        self._client = client
        self._ns = namespace

    async def create_job(self, manifest: JsonDict) -> None:
        with _upstream(409):  # already exists: the handler was retried
            await self._client.create(
                cast(Job, Job.from_dict(manifest)), field_manager=FIELD_MANAGER
            )

    async def get_job(self, name: str) -> JsonDict | None:
        with _upstream(404):
            job = await self._client.get(Job, name, namespace=self._ns)
            return cast(JsonDict, job.to_dict())
        return None

    async def delete_job(self, name: str) -> None:
        with _upstream(404):
            await self._client.delete(Job, name, namespace=self._ns, cascade=CascadeType.BACKGROUND)

    async def pod_log(self, job_name: str) -> str:
        with _upstream(400, 404):  # pod gone, or its container never started
            pod = await self._latest_pod(job_name)
            if pod is None or pod.metadata is None or pod.metadata.name is None:
                return ""
            lines = [
                line
                async for line in self._client.log(
                    pod.metadata.name, namespace=self._ns, container=WORKER_CONTAINER
                )
            ]
            return "\n".join(lines)
        return ""

    async def get_task(self, name: str) -> PlatformTask | None:
        with _upstream(404):
            obj = await self._client.get(Task, name, namespace=self._ns)
            return task_from_body(cast(dict[str, Any], obj.to_dict()))
        return None

    async def patch_task_status(self, name: str, status: TaskStatus) -> None:
        # exclude_none=False on purpose: in a merge patch a null deletes the key, so the
        # "running" message does not outlive the final status.
        body = {"status": status.model_dump(mode="json")}
        with _upstream():
            await self._client.patch(
                Task.Status,
                name,
                body,
                namespace=self._ns,
                patch_type=PatchType.MERGE,
                field_manager=FIELD_MANAGER,
            )

    async def delete_task(self, name: str) -> None:
        with _upstream(404):
            await self._client.delete(
                Task, name, namespace=self._ns, cascade=CascadeType.BACKGROUND
            )

    async def _latest_pod(self, job_name: str) -> Pod | None:
        latest: Pod | None = None
        async for pod in self._client.list(Pod, namespace=self._ns, labels={"job-name": job_name}):
            created = pod.metadata.creationTimestamp if pod.metadata else None
            held = latest.metadata.creationTimestamp if latest and latest.metadata else None
            if latest is None or (created and held and created >= held):
                latest = pod
        return latest
