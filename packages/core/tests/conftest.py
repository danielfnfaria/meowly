from collections.abc import AsyncIterator
from typing import Any

import pytest
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.pool import StaticPool

from meowly_core import Base, Core, Database, InMemoryTaskStore, build_core


def enable_sqlite_foreign_keys(engine: AsyncEngine) -> None:
    """SQLite ignores foreign keys unless asked per connection; Postgres never does. Without
    this no test can see a constraint fire, which is how a 500 on delete went unnoticed."""

    @event.listens_for(engine.sync_engine, "connect")
    def _on_connect(dbapi_connection: Any, _: object) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


@pytest.fixture
async def database() -> AsyncIterator[Database]:
    # StaticPool: every connection must see the same in-memory SQLite database.
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    enable_sqlite_foreign_keys(engine)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    db = Database(engine)
    yield db
    await db.dispose()


@pytest.fixture
async def session(database: Database) -> AsyncIterator[AsyncSession]:
    async with database.session() as s:
        yield s


@pytest.fixture
def core(session: AsyncSession) -> Core:
    return build_core(session, tasks=InMemoryTaskStore())
