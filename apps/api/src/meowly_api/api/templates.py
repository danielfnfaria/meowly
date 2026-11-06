"""Template catalog: HTTP over `core.templates`; the rules live in the service."""

from collections.abc import Sequence
from typing import Annotated

from fastapi import APIRouter, Path, status

from meowly_api.api.deps import CoreDep
from meowly_api.schemas.catalog import TemplateCreate, TemplateOut, TemplateUpdate

router = APIRouter(prefix="/templates", tags=["templates"])

Slug = Annotated[str, Path(description="Unique, URL-safe identifier of the template")]


@router.get("", operation_id="list_templates")
async def list_templates(core: CoreDep) -> Sequence[TemplateOut]:
    return [TemplateOut.model_validate(e) for e in await core.templates.list()]


@router.post("", operation_id="create_template", status_code=status.HTTP_201_CREATED)
async def create_template(body: TemplateCreate, core: CoreDep) -> TemplateOut:
    entity = await core.templates.create(**body.model_dump())
    return TemplateOut.model_validate(entity)


@router.get("/{slug}", operation_id="get_template")
async def get_template(slug: Slug, core: CoreDep) -> TemplateOut:
    return TemplateOut.model_validate(await core.templates.get_by_slug(slug))


@router.patch("/{slug}", operation_id="update_template")
async def update_template(slug: Slug, body: TemplateUpdate, core: CoreDep) -> TemplateOut:
    return TemplateOut.model_validate(await core.templates.update(slug, body.fields()))


@router.delete("/{slug}", operation_id="delete_template", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(slug: Slug, core: CoreDep) -> None:
    await core.templates.delete(slug)
