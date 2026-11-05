import uuid

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from purr_core.models.base import Base, EntityMixin


class Owner(EntityMixin, Base):
    __tablename__ = "owners"

    name: Mapped[str] = mapped_column(sa.String(200))
    email: Mapped[str | None] = mapped_column(sa.String(320), default=None)


class Component(EntityMixin, Base):
    __tablename__ = "components"

    name: Mapped[str] = mapped_column(sa.String(200))
    description: Mapped[str | None] = mapped_column(sa.Text, default=None)
    owner_id: Mapped[uuid.UUID] = mapped_column(sa.ForeignKey("owners.id"))
    repo_url: Mapped[str | None] = mapped_column(sa.String(500), default=None)
    system: Mapped[str | None] = mapped_column(sa.String(100), default=None)


class Template(EntityMixin, Base):
    __tablename__ = "templates"

    name: Mapped[str] = mapped_column(sa.String(200))
    description: Mapped[str | None] = mapped_column(sa.Text, default=None)
    source_url: Mapped[str] = mapped_column(sa.String(500))
    source_path: Mapped[str | None] = mapped_column(sa.String(500), default=None)
    # sa.JSON (not JSONB): portable to the SQLite the tests run on.
    inputs: Mapped[dict[str, str]] = mapped_column(sa.JSON, default=dict)


class Environment(EntityMixin, Base):
    __tablename__ = "environments"

    name: Mapped[str] = mapped_column(sa.String(200))
    description: Mapped[str | None] = mapped_column(sa.Text, default=None)
