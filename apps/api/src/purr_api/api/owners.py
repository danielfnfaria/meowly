"""Owner catalog: HTTP over `core.owners`; the rules live in the service."""

from collections.abc import Sequence
from typing import Annotated

from fastapi import APIRouter, Path, status

from purr_api.api.deps import CoreDep
from purr_api.schemas.catalog import OwnerCreate, OwnerOut, OwnerUpdate

router = APIRouter(prefix="/owners", tags=["owners"])

Slug = Annotated[str, Path(description="Unique, URL-safe identifier of the owner")]


@router.get("", operation_id="list_owners")
async def list_owners(core: CoreDep) -> Sequence[OwnerOut]:
    return [OwnerOut.model_validate(e) for e in await core.owners.list()]


@router.post("", operation_id="create_owner", status_code=status.HTTP_201_CREATED)
async def create_owner(body: OwnerCreate, core: CoreDep) -> OwnerOut:
    entity = await core.owners.create(**body.model_dump())
    return OwnerOut.model_validate(entity)


@router.get("/{slug}", operation_id="get_owner")
async def get_owner(slug: Slug, core: CoreDep) -> OwnerOut:
    return OwnerOut.model_validate(await core.owners.get_by_slug(slug))


@router.patch("/{slug}", operation_id="update_owner")
async def update_owner(slug: Slug, body: OwnerUpdate, core: CoreDep) -> OwnerOut:
    return OwnerOut.model_validate(await core.owners.update(slug, body.fields()))


@router.delete("/{slug}", operation_id="delete_owner", status_code=status.HTTP_204_NO_CONTENT)
async def delete_owner(slug: Slug, core: CoreDep) -> None:
    await core.owners.delete(slug)
