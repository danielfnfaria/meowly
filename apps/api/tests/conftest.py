from collections.abc import AsyncGenerator
from pathlib import Path

import httpx
import pytest
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import StaticPool

from purr_api.api.deps import AppState
from purr_api.main import create_app
from purr_api.settings import Settings
from purr_core import Base, Database, InMemoryTaskStore


def make_settings(ui_dir: Path | None = None) -> Settings:
    return Settings(
        database_url="sqlite+aiosqlite://",
        launcher="memory",
        ui_dir=str(ui_dir) if ui_dir else None,
    )


@pytest.fixture
async def state() -> AsyncGenerator[AppState]:
    # StaticPool: every session shares the one in-memory connection, so the schema created
    # here is the one the requests see.
    engine = create_async_engine("sqlite+aiosqlite://", poolclass=StaticPool)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    db = Database(engine)
    yield AppState(settings=make_settings(), db=db, tasks=InMemoryTaskStore("purr"))
    await db.dispose()


@pytest.fixture
async def client(state: AppState) -> AsyncGenerator[httpx.AsyncClient]:
    transport = httpx.ASGITransport(app=create_app(state=state))
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as http_client:
        yield http_client
