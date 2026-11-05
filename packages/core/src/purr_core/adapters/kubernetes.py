import uuid
from collections.abc import Mapping
from typing import Any, cast

from lightkube import ApiError, AsyncClient
from lightkube.generic_resource import (
    create_namespaced_resource,  # pyright: ignore[reportUnknownVariableType]
)
from pydantic import ValidationError

from purr_contracts import (
    GROUP,
    KIND,
    PLURAL,
    VERSION,
    NotFoundError,
    PlatformTask,
    TaskSpec,
    UpstreamError,
    task_body,
    task_from_body,
)

# lightkube builds the class from the CRD coordinates at runtime, so it needs no generated
# model and works for a CRD installed after this process started.
# Any: lightkube's generic resource classes are built at runtime and carry no usable types.
_PlatformTaskResource: Any = create_namespaced_resource(GROUP, VERSION, KIND, PLURAL)


class KubernetesTaskStore:
    """Tasks as PlatformTask custom resources in `namespace`. The controller reconciles them;
    this adapter only creates and reads."""

    def __init__(self, namespace: str, client: AsyncClient | None = None) -> None:
        self._namespace = namespace
        # Any: lightkube's overloaded, runtime-built resource types do not type-check; every
        # result is converted to a PlatformTask at the boundary (`_parse`).
        self._client: Any = client or AsyncClient(namespace=namespace)

    async def create(
        self,
        spec: TaskSpec,
        *,
        name: str | None = None,
        labels: Mapping[str, str] | None = None,
    ) -> PlatformTask:
        task_name = name or f"task-{uuid.uuid4().hex[:10]}"
        body = task_body(task_name, namespace=self._namespace, spec=spec, labels=labels)
        try:
            created = await self._client.create(
                _PlatformTaskResource.from_dict(body), namespace=self._namespace
            )
        except ApiError as exc:
            raise self._upstream(exc) from exc
        return self._parse(created)

    async def list(self) -> list[PlatformTask]:
        try:
            return [
                self._parse(item)
                async for item in self._client.list(
                    _PlatformTaskResource, namespace=self._namespace
                )
            ]
        except ApiError as exc:
            raise self._upstream(exc) from exc

    async def get(self, name: str) -> PlatformTask:
        try:
            found = await self._client.get(_PlatformTaskResource, name, namespace=self._namespace)
        except ApiError as exc:
            if exc.status.code == 404:
                raise NotFoundError(f"task {name!r} not found", code="task_not_found") from exc
            raise self._upstream(exc) from exc
        return self._parse(found)

    async def close(self) -> None:
        # The client keeps an httpx connection pool open; closing it at shutdown avoids
        # leaking sockets and the "unclosed client" warning.
        await self._client.close()

    @staticmethod
    def _parse(resource: Any) -> PlatformTask:
        body = cast("dict[str, Any]", resource.to_dict())
        try:
            return task_from_body(body)
        except ValidationError as exc:
            raise UpstreamError("the cluster returned a malformed PlatformTask") from exc

    @staticmethod
    def _upstream(exc: ApiError) -> UpstreamError:
        # The cluster's message can name internals; it goes to the log, not to the client.
        return UpstreamError(f"kubernetes answered {exc.status.code}")
