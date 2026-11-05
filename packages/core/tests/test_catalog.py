import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from purr_contracts import ConflictError, NotFoundError
from purr_core import Core, Database, Owner
from purr_core.repositories import OwnerRepository


async def test_repository_add_get_by_slug_delete(session: AsyncSession) -> None:
    repo = OwnerRepository(session)
    owner = await repo.add(Owner(slug="team-a", name="Team A"))
    assert isinstance(owner.id, uuid.UUID)
    assert owner.created_at.tzinfo is not None
    assert await repo.get(owner.id) is owner
    assert await repo.get_by_slug("team-a") is owner
    assert await repo.get_by_slug("nope") is None
    assert [o.slug for o in await repo.list()] == ["team-a"]
    await repo.delete(owner)
    assert await repo.get_by_slug("team-a") is None


async def test_owner_conflict_and_not_found(core: Core) -> None:
    await core.owners.create("team-a", "Team A")
    with pytest.raises(ConflictError):
        await core.owners.create("team-a", "Again")
    with pytest.raises(NotFoundError):
        await core.owners.get_by_slug("missing")
    with pytest.raises(NotFoundError):
        await core.owners.delete("missing")


async def test_owner_update_and_delete(core: Core) -> None:
    await core.owners.create("team-a", "Team A")
    updated = await core.owners.update("team-a", {"name": "Renamed", "email": "a@x.io"})
    assert (updated.name, updated.email) == ("Renamed", "a@x.io")
    await core.owners.delete("team-a")
    assert list(await core.owners.list()) == []


async def test_component_requires_owner(core: Core) -> None:
    with pytest.raises(NotFoundError):
        await core.components.create("svc", "Svc", uuid.uuid4())
    owner = await core.owners.create("team-a", "Team A")
    component = await core.components.create("svc", "Svc", owner.id, system="payments")
    assert component.owner_id == owner.id
    with pytest.raises(ConflictError):
        await core.components.create("svc", "Svc 2", owner.id)
    updated = await core.components.update("svc", {"repo_url": "https://git/x"})
    assert updated.repo_url == "https://git/x"


async def test_template_inputs_roundtrip(core: Core) -> None:
    template = await core.templates.create(
        "go-service", "Go service", "https://git/t", inputs={"name": "string"}
    )
    assert (await core.templates.get_by_slug("go-service")).inputs == {"name": "string"}
    assert template.source_path is None


async def test_environment_crud(core: Core) -> None:
    await core.environments.create("dev", "Development")
    await core.environments.update("dev", {"description": "d"})
    assert (await core.environments.get_by_slug("dev")).description == "d"
    await core.environments.delete("dev")
    with pytest.raises(NotFoundError):
        await core.environments.get_by_slug("dev")


async def test_session_commits_and_rolls_back(database: Database) -> None:
    async with database.session() as s:
        await OwnerRepository(s).add(Owner(slug="kept", name="Kept"))
    with pytest.raises(RuntimeError):
        async with database.session() as s:
            await OwnerRepository(s).add(Owner(slug="lost", name="Lost"))
            raise RuntimeError("boom")
    async with database.session() as s:
        repo = OwnerRepository(s)
        assert await repo.get_by_slug("kept") is not None
        assert await repo.get_by_slug("lost") is None
