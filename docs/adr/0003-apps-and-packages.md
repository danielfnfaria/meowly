# 0003: apps and packages

Status: accepted (2026-11-05).

## Context

meowly is a monorepo of three processes (API, controller, worker) that share a wire format and
some plumbing. In every monorepo that grows without a rule, one process ends up importing
another to get at a library it happens to hold; the images get heavier, the boundaries blur,
and a change to the API breaks the pod that runs tasks.

## Decision

1. **An app is one process and one image** (`apps/<name>`, its own `Dockerfile` and
   entrypoint) and **never imports another app**.
2. **Shared code lives in `packages/`**: distribution `meowly-<name>`, Python package
   `meowly_<name>`, same layout as an app (`pyproject.toml`, `src/<package>/` with `py.typed`,
   `tests/`), no `Dockerfile`.
3. **Dependency directions**: apps → packages, never apps → apps; packages never import apps.
   The layers are `contracts` ← `core` ← `http` and `contracts` ← `engine`, with `runtime` as
   a leaf everyone uses.
   - `meowly_contracts` imports no other workspace package: it is the wire (specs, statuses,
     events, the CR envelope, the domain errors).
   - `meowly_runtime` is process plumbing only (structlog + pydantic-settings): JSON logging and
     the bind settings. It imports no workspace package either.
   - `meowly_engine` imports neither `meowly_core` nor `meowly_http`: it runs inside a worker pod
     that has no database and serves no HTTP (ADR 0002).
   - `meowly_core` imports neither `meowly_engine` nor `meowly_http`: the catalog knows nothing
     about executing a task or about HTTP.
   - **The controller and the worker import neither `meowly_core` nor `meowly_http`**: the
     controller only turns a CR into a Job, and the worker only runs the spec it was handed.
     Their images carry no SQLAlchemy, no Alembic and no web framework.
4. **import-linter enforces it**, not a review habit: the contracts live in
   `[tool.importlinter]` of the root `pyproject.toml` and `uv run lint-imports` runs in
   `make check` and in CI. The independence contract also catches indirect paths
   (app → package → app).
5. `apps/ui` is outside the `uv` workspace (`exclude`), has its own `package.json`, and is
   ignored by ruff and pyright. It is built inside the API image and served by the API
   (ADR 0004).

## Consequences

- A new process is a new app; code two processes need goes to a package first.
- A boundary violation fails `make check` instead of being discovered later as a bloated image
  or an import cycle.
- Each `Dockerfile` copies only the packages its app needs (plus every member's
  `pyproject.toml`, which `uv sync --frozen` requires).
- The cost is more packages than a flat `src/` would have, and a new shared helper needs a
  decision about where it belongs. That decision is the point.
