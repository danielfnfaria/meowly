"""Tasks. The API only records the request and reads it back: nothing runs in this process
(ADR 0002). The controller turns the PlatformTask into a Job.

With `PURR_LAUNCHER=memory` the store is the `InMemoryTaskStore`: the task is kept in the API
process as `pending` and nothing executes it. That is how `make up` (compose, no cluster)
works, and it is enough to develop the catalog and the UI.
"""

from collections.abc import Sequence
from typing import Annotated

from fastapi import APIRouter, Path, status

from purr_api.api.deps import CoreDep
from purr_api.schemas.tasks import TaskCreate, TaskOut
from purr_contracts import TaskSpec

router = APIRouter(prefix="/tasks", tags=["tasks"])

# Until there is authentication, the requester is not known; the field exists on the spec so
# the worker and the audit trail do not change shape when it is.
ANONYMOUS = "anonymous"


@router.post("", operation_id="create_task", status_code=status.HTTP_201_CREATED)
async def create_task(body: TaskCreate, core: CoreDep) -> TaskOut:
    spec = TaskSpec(**body.model_dump(), requested_by=ANONYMOUS)
    return TaskOut.from_task(await core.tasks.create(spec))


@router.get("", operation_id="list_tasks")
async def list_tasks(core: CoreDep) -> Sequence[TaskOut]:
    return [TaskOut.from_task(t) for t in await core.tasks.list()]


@router.get("/{name}", operation_id="get_task")
async def get_task(
    name: Annotated[str, Path(description="Name of the PlatformTask")], core: CoreDep
) -> TaskOut:
    return TaskOut.from_task(await core.tasks.get(name))
