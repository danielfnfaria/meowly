import uuid
from datetime import UTC, datetime

import sqlalchemy as sa
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# Deterministic constraint names: migrations can drop them by name on any backend.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = sa.MetaData(naming_convention=NAMING_CONVENTION)


def _now() -> datetime:
    return datetime.now(UTC)


class EntityMixin:
    """Primary key, unique slug and timestamps every catalog entity has."""

    slug: Mapped[str] = mapped_column(sa.String(100), unique=True, index=True)
    id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    # Python-side defaults (not server_default): the same code works on Postgres and SQLite.
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), default=_now, onupdate=_now
    )
