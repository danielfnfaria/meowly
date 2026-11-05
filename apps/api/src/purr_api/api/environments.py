"""Environment catalog: HTTP over `core.environments`; the rules live in the service."""

from collections.abc import Sequence
from typing import Annotated

from fastapi import APIRouter, Path, status

from purr_api.api.deps import CoreDep
from purr_api.schemas.catalog import EnvironmentCreate, EnvironmentOut, EnvironmentUpdate

router = APIRouter(prefix="/environments", tags=["environments"])

Slug = Annotated[str, Path(description="Unique, URL-safe identifier of the environment")]


@router.get("", operation_id="list_environments")
async def list_environments(core: CoreDep) -> Sequence[EnvironmentOut]:
    return [EnvironmentOut.model_validate(e) for e in await core.environments.list()]


@router.post("", operation_id="create_environment", status_code=status.HTTP_201_CREATED)
async def create_environment(body: EnvironmentCreate, core: CoreDep) -> EnvironmentOut:
    entity = await core.environments.create(**body.model_dump())
    return EnvironmentOut.model_validate(entity)


@router.get("/{slug}", operation_id="get_environment")
async def get_environment(slug: Slug, core: CoreDep) -> EnvironmentOut:
    return EnvironmentOut.model_validate(await core.environments.get_by_slug(slug))


@router.patch("/{slug}", operation_id="update_environment")
async def update_environment(slug: Slug, body: EnvironmentUpdate, core: CoreDep) -> EnvironmentOut:
    return EnvironmentOut.model_validate(await core.environments.update(slug, body.fields()))


@router.delete("/{slug}", operation_id="delete_environment", status_code=status.HTTP_204_NO_CONTENT)
async def delete_environment(slug: Slug, core: CoreDep) -> None:
    await core.environments.delete(slug)
