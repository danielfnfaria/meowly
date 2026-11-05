"""Dump the OpenAPI document, the contract with the UI (its TypeScript client is generated
from it, `make check-openapi`).

Usage: python -m purr_api.openapi > openapi.json
"""

import json
import sys

from purr_api.main import create_app
from purr_api.settings import Settings
from purr_runtime import configure_logging


def main() -> None:
    # Describing the API needs no real config, no environment and no database: the settings
    # are built here, so a stray PURR_* variable cannot change the document. Nothing connects
    # (no lifespan runs).
    # stdout is the document: logs (the missing-UI warning) go to stderr.
    configure_logging("WARNING", stream="stderr")
    settings = Settings(
        database_url="postgresql+asyncpg://x:x@localhost/x",
        launcher="memory",
        ui_dir=None,
    )
    json.dump(create_app(settings).openapi(), sys.stdout, indent=2)


if __name__ == "__main__":
    main()
