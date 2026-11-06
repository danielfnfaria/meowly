"""The admin UI's build (apps/ui `dist/`), served by the API on the same origin (ADR 0004).

One server delivers the single-page app and its API: no separate image, no proxy, no CORS.

- `/assets/*` are content-hashed by Vite: cached for a year;
- any other path that is a file of the build is served as is (favicon...);
- everything else that is not an API path falls back to `index.html` (client-side routes),
  never cached so a new deploy is picked up on the next load.
"""

from pathlib import Path

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse

# Paths owned by the API: an unknown one is a 404, not the SPA (a typo in /v1/... must not
# answer 200 with HTML).
API_PREFIXES = ("v1", "healthz")
IMMUTABLE = "public, max-age=31536000, immutable"
REVALIDATE = "no-cache"


def ui_router(dist: Path) -> APIRouter:
    """Routes serving the UI build in `dist` (must contain index.html)."""
    root = dist.resolve()
    index = root / "index.html"
    router = APIRouter(include_in_schema=False)

    @router.get("/{path:path}")
    async def serve(path: str) -> FileResponse:
        first = path.split("/", 1)[0]
        if first in API_PREFIXES:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="not found")
        candidate = (root / path).resolve()
        # Only files inside the build (no `..` escapes); directories fall back to the SPA.
        if path and candidate.is_relative_to(root) and candidate.is_file():
            cache = IMMUTABLE if first == "assets" else REVALIDATE
            return FileResponse(candidate, headers={"Cache-Control": cache})
        return FileResponse(index, headers={"Cache-Control": REVALIDATE})

    return router
