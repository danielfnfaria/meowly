import uuid
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from purr_core.models import EntityMixin


class Repository[T: EntityMixin]:
    """Generic access to one table. Services write only through repositories."""

    model: type[T]

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, entity: T) -> T:
        self._session.add(entity)
        # flush so the unique constraint fires here, where the caller can translate it,
        # not at commit time.
        await self._session.flush()
        return entity

    async def get(self, id_: uuid.UUID) -> T | None:
        return await self._session.get(self.model, id_)

    async def get_by_slug(self, slug: str) -> T | None:
        result = await self._session.execute(sa.select(self.model).where(self.model.slug == slug))
        return result.scalar_one_or_none()

    async def list(self) -> Sequence[T]:
        result = await self._session.execute(sa.select(self.model).order_by(self.model.slug))
        return result.scalars().all()

    async def delete(self, entity: T) -> None:
        await self._session.delete(entity)
        await self._session.flush()

    async def flush(self) -> None:
        """Persist pending changes to an entity already loaded (an update)."""
        await self._session.flush()
