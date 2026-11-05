import uuid
from typing import ClassVar, cast

from pydantic import Field

from purr_api.schemas.base import Body, EntityOut, Patch
from purr_core.services.catalog import (
    ComponentFields,
    EnvironmentFields,
    OwnerFields,
    TemplateFields,
)

# Slugs end up in URLs and in Kubernetes labels (the component slug is a label value): keep
# them to lowercase DNS-label-like words.
Slug = Field(min_length=1, max_length=63, pattern=r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?$")
Name = Field(min_length=1, max_length=200)


class OwnerCreate(Body):
    slug: str = Slug
    name: str = Name
    email: str | None = Field(default=None, max_length=320)


class OwnerUpdate(Patch):
    NULLABLE: ClassVar[frozenset[str]] = frozenset({"email"})
    name: str | None = Field(default=None, min_length=1, max_length=200)
    email: str | None = Field(default=None, max_length=320)

    def fields(self) -> OwnerFields:
        # The validator above guarantees the keys are a subset of OwnerFields.
        return cast("OwnerFields", self.sent())


class OwnerOut(EntityOut):
    name: str
    email: str | None


class ComponentCreate(Body):
    slug: str = Slug
    name: str = Name
    owner_id: uuid.UUID
    description: str | None = None
    repo_url: str | None = Field(default=None, max_length=500)
    system: str | None = Field(default=None, max_length=100)


class ComponentUpdate(Patch):
    NULLABLE: ClassVar[frozenset[str]] = frozenset({"description", "repo_url", "system"})
    name: str | None = Field(default=None, min_length=1, max_length=200)
    owner_id: uuid.UUID | None = None
    description: str | None = None
    repo_url: str | None = Field(default=None, max_length=500)
    system: str | None = Field(default=None, max_length=100)

    def fields(self) -> ComponentFields:
        return cast("ComponentFields", self.sent())


class ComponentOut(EntityOut):
    name: str
    description: str | None
    owner_id: uuid.UUID
    repo_url: str | None
    system: str | None


class TemplateCreate(Body):
    slug: str = Slug
    name: str = Name
    source_url: str = Field(min_length=1, max_length=500)
    description: str | None = None
    source_path: str | None = Field(default=None, max_length=500)
    inputs: dict[str, str] = Field(default_factory=dict[str, str])


class TemplateUpdate(Patch):
    NULLABLE: ClassVar[frozenset[str]] = frozenset({"description", "source_path"})
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    source_url: str | None = Field(default=None, min_length=1, max_length=500)
    source_path: str | None = Field(default=None, max_length=500)
    inputs: dict[str, str] | None = None

    def fields(self) -> TemplateFields:
        return cast("TemplateFields", self.sent())


class TemplateOut(EntityOut):
    name: str
    description: str | None
    source_url: str
    source_path: str | None
    inputs: dict[str, str]


class EnvironmentCreate(Body):
    slug: str = Slug
    name: str = Name
    description: str | None = None


class EnvironmentUpdate(Patch):
    NULLABLE: ClassVar[frozenset[str]] = frozenset({"description"})
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None

    def fields(self) -> EnvironmentFields:
        return cast("EnvironmentFields", self.sent())


class EnvironmentOut(EntityOut):
    name: str
    description: str | None
