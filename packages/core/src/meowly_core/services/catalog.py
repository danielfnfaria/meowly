import uuid
from collections.abc import Callable, Sequence
from typing import TypedDict

from sqlalchemy.exc import IntegrityError

from meowly_contracts import ConflictError, NotFoundError
from meowly_core.models import Component, EntityMixin, Environment, Owner, Template
from meowly_core.repositories import (
    ComponentRepository,
    EnvironmentRepository,
    OwnerRepository,
    Repository,
    TemplateRepository,
)


class OwnerFields(TypedDict, total=False):
    name: str
    email: str | None


class ComponentFields(TypedDict, total=False):
    name: str
    description: str | None
    owner_id: uuid.UUID
    repo_url: str | None
    system: str | None


class TemplateFields(TypedDict, total=False):
    name: str
    description: str | None
    source_url: str
    source_path: str | None
    inputs: dict[str, str]


class EnvironmentFields(TypedDict, total=False):
    name: str
    description: str | None


class _CatalogService[T: EntityMixin]:
    """create/list/get_by_slug/update/delete shared by the four entities."""

    label: str

    def __init__(self, repo: Repository[T]) -> None:
        self._repo = repo

    async def _create(self, entity: T) -> T:
        if await self._repo.get_by_slug(entity.slug) is not None:
            raise ConflictError(f"{self.label} {entity.slug!r} already exists")
        try:
            return await self._repo.add(entity)
        except IntegrityError as exc:
            # Lost the race against a concurrent insert of the same slug.
            raise ConflictError(f"{self.label} {entity.slug!r} already exists") from exc

    async def list(self) -> Sequence[T]:
        return await self._repo.list()

    async def get_by_slug(self, slug: str) -> T:
        entity = await self._repo.get_by_slug(slug)
        if entity is None:
            raise NotFoundError(f"{self.label} {slug!r} not found")
        return entity

    async def _update(self, slug: str, fields: Callable[[T], None]) -> T:
        entity = await self.get_by_slug(slug)
        fields(entity)
        await self._repo.flush()
        return entity

    async def delete(self, slug: str) -> None:
        entity = await self.get_by_slug(slug)
        try:
            await self._repo.delete(entity)
        except IntegrityError as exc:
            # The translation lives here, not in the generic repository: only the service
            # knows the caller can fix this (remove what still points at the entity) and so
            # that it is a conflict, not a 500. The FK is what enforces it, in the database.
            raise ConflictError(
                f"{self.label} {slug!r} is still referenced by other objects"
            ) from exc


def _apply(entity: object, fields: dict[str, object]) -> None:
    for key, value in fields.items():
        setattr(entity, key, value)


class OwnerService(_CatalogService[Owner]):
    label = "owner"

    def __init__(self, repo: OwnerRepository) -> None:
        super().__init__(repo)

    async def create(self, slug: str, name: str, email: str | None = None) -> Owner:
        return await self._create(Owner(slug=slug, name=name, email=email))

    async def update(self, slug: str, fields: OwnerFields) -> Owner:
        return await self._update(slug, lambda e: _apply(e, dict(fields)))


class ComponentService(_CatalogService[Component]):
    label = "component"

    def __init__(self, repo: ComponentRepository, owners: OwnerRepository) -> None:
        super().__init__(repo)
        self._owners = owners

    async def _require_owner(self, owner_id: uuid.UUID) -> None:
        if await self._owners.get(owner_id) is None:
            raise NotFoundError(f"owner {owner_id} not found")

    async def create(
        self,
        slug: str,
        name: str,
        owner_id: uuid.UUID,
        description: str | None = None,
        repo_url: str | None = None,
        system: str | None = None,
    ) -> Component:
        await self._require_owner(owner_id)
        return await self._create(
            Component(
                slug=slug,
                name=name,
                owner_id=owner_id,
                description=description,
                repo_url=repo_url,
                system=system,
            )
        )

    async def update(self, slug: str, fields: ComponentFields) -> Component:
        if "owner_id" in fields:
            await self._require_owner(fields["owner_id"])
        return await self._update(slug, lambda e: _apply(e, dict(fields)))


class TemplateService(_CatalogService[Template]):
    label = "template"

    def __init__(self, repo: TemplateRepository) -> None:
        super().__init__(repo)

    async def create(
        self,
        slug: str,
        name: str,
        source_url: str,
        description: str | None = None,
        source_path: str | None = None,
        inputs: dict[str, str] | None = None,
    ) -> Template:
        return await self._create(
            Template(
                slug=slug,
                name=name,
                source_url=source_url,
                description=description,
                source_path=source_path,
                inputs=inputs or {},
            )
        )

    async def update(self, slug: str, fields: TemplateFields) -> Template:
        return await self._update(slug, lambda e: _apply(e, dict(fields)))


class EnvironmentService(_CatalogService[Environment]):
    label = "environment"

    def __init__(self, repo: EnvironmentRepository) -> None:
        super().__init__(repo)

    async def create(self, slug: str, name: str, description: str | None = None) -> Environment:
        return await self._create(Environment(slug=slug, name=name, description=description))

    async def update(self, slug: str, fields: EnvironmentFields) -> Environment:
        return await self._update(slug, lambda e: _apply(e, dict(fields)))
