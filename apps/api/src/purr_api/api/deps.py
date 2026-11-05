"""Composition root of a request: where the process-wide state becomes the `Core` a router uses.

Routers depend on `CoreDep` and call its services; they never see a session, a repository or
an adapter.
"""

from collections.abc import AsyncGenerator
from dataclasses import dataclass
from typing import Annotated, cast

from fastapi import Depends, Request

from purr_api.settings import Settings
from purr_core import Core, Database, TaskStore, build_core


@dataclass
class AppState:
    """What lives as long as the process. Tests build one with in-memory adapters."""

    settings: Settings
    db: Database
    tasks: TaskStore


def get_state(request: Request) -> AppState:
    # `app.state` is untyped (Any) by Starlette's design; `build_app` stores the AppState there.
    return cast("AppState", request.app.state.container)


StateDep = Annotated[AppState, Depends(get_state)]


async def get_core(state: StateDep) -> AsyncGenerator[Core]:
    """One session (one unit of work) per request: commit on success, rollback on error."""
    async with state.db.session() as session:
        yield build_core(session, tasks=state.tasks)


# scope="function": the exit code (the commit) runs before the response is sent. With the
# default scope it runs after, so a client could read its own write before it was committed,
# and a failing commit would already have answered 2xx.
CoreDep = Annotated[Core, Depends(get_core, scope="function")]
