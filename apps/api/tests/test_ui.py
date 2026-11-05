from pathlib import Path

import httpx

from purr_api.api.deps import AppState
from purr_api.main import create_app


async def test_without_a_built_ui_the_api_still_serves_itself(
    state: AppState, tmp_path: Path
) -> None:
    # ui_dir points at a directory with no index.html: the state before the UI exists.
    state.settings.ui_dir = str(tmp_path)
    transport = httpx.ASGITransport(app=create_app(state=state))
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        assert (await client.get("/v1/info")).status_code == 200
        assert (await client.get("/")).status_code == 404


async def test_the_ui_falls_back_to_index_and_never_shadows_the_api(
    state: AppState, tmp_path: Path
) -> None:
    (tmp_path / "index.html").write_text("<html>purr</html>")
    state.settings.ui_dir = str(tmp_path)
    transport = httpx.ASGITransport(app=create_app(state=state))
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        assert "purr" in (await client.get("/components/billing")).text
        assert (await client.get("/v1/info")).status_code == 200
        assert (await client.get("/v1/nope")).status_code == 404
        assert (await client.get("/healthz/ready")).status_code == 200
