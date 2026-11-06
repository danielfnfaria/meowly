"""The cluster, as far as the handlers need it. Everything is namespaced to the execution
namespace the adapter was built for: the controller has no ClusterRole."""

from typing import Protocol

from meowly_contracts import JsonDict, PlatformTask, TaskStatus


class Kube(Protocol):
    async def create_job(self, manifest: JsonDict) -> None:
        """Create the Job. An already existing one is not an error: handlers are retried."""
        ...

    async def get_job(self, name: str) -> JsonDict | None: ...

    async def pod_log(self, job_name: str) -> str:
        """The log of the (latest) pod of the Job; empty when there is no pod or no log yet."""
        ...

    async def get_task(self, name: str) -> PlatformTask | None: ...

    async def patch_task_status(self, name: str, status: TaskStatus) -> None:
        """Write `status` onto the CR's status subresource (the controller is its only writer)."""
        ...

    async def delete_task(self, name: str) -> None: ...
