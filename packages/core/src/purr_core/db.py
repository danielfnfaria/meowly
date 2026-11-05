from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from purr_core.settings import CoreSettings


class Database:
    """The async engine and the session factory of one process."""

    def __init__(self, engine: AsyncEngine) -> None:
        self.engine = engine
        # expire_on_commit=False: services return ORM objects after the unit of work ended,
        # and a lazy refresh on an async session would fail.
        self._sessions = async_sessionmaker(engine, expire_on_commit=False)

    @classmethod
    def from_settings(cls, cfg: CoreSettings) -> "Database":
        if cfg.database_url.startswith("sqlite"):
            # SQLite has no pool sizing; pool_size/max_overflow would be rejected.
            return cls(create_async_engine(cfg.database_url))
        return cls(
            create_async_engine(
                cfg.database_url,
                pool_size=cfg.db_pool_size,
                max_overflow=cfg.db_max_overflow,
                # A connection the server dropped (failover, idle timeout) is replaced instead
                # of failing the first request that picks it.
                pool_pre_ping=True,
            )
        )

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession]:
        """One unit of work: commits on success, rolls back on any error."""
        async with self._sessions() as session:
            try:
                yield session
                await session.commit()
            except BaseException:
                await session.rollback()
                raise

    async def dispose(self) -> None:
        await self.engine.dispose()
