"""Component catalog: HTTP over `core.components`; the rules live in the service."""

from collections.abc import Sequence
from typing import Annotated

from fastapi import APIRouter, Path, status

from purr_api.api.deps import CoreDep
from purr_api.schemas.catalog import ComponentCreate, ComponentOut, ComponentUpdate

router = APIRouter(prefix="/components", tags=["components"])

Slug = Annotated[str, Path(description="Unique, URL-safe identifier of the component")]


@router.get("", operation_id="list_components")
async def list_components(core: CoreDep) -> Sequence[ComponentOut]:
    return [ComponentOut.model_validate(e) for e in await core.components.list()]


@router.post("", operation_id="create_component", status_code=status.HTTP_201_CREATED)
async def create_component(body: ComponentCreate, core: CoreDep) -> ComponentOut:
    entity = await core.components.create(**body.model_dump())
    return ComponentOut.model_validate(entity)


@router.get("/{slug}", operation_id="get_component")
async def get_component(slug: Slug, core: CoreDep) -> ComponentOut:
    return ComponentOut.model_validate(await core.components.get_by_slug(slug))


@router.patch("/{slug}", operation_id="update_component")
async def update_component(slug: Slug, body: ComponentUpdate, core: CoreDep) -> ComponentOut:
    return ComponentOut.model_validate(await core.components.update(slug, body.fields()))


@router.delete("/{slug}", operation_id="delete_component", status_code=status.HTTP_204_NO_CONTENT)
async def delete_component(slug: Slug, core: CoreDep) -> None:
    await core.components.delete(slug)
