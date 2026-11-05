from collections.abc import AsyncIterator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import StaticPool

from purr_core import Base, Core, Database, InMemoryTaskStore, build_core


@pytest.fixture
async def database() -> AsyncIterator[Database]:
    # StaticPool: every connection must see the same in-memory SQLite database.
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
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
