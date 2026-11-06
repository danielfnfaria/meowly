# Build context is the monorepo root (see skaffold.yaml).
# The API also serves the admin UI (ADR 0004): its build is made here with Node and copied in
# as static files; Node is not in the final image.
FROM node:22-alpine AS ui
WORKDIR /ui
COPY apps/ui/package.json apps/ui/package-lock.json ./
RUN --mount=type=cache,target=/root/.npm npm ci --ignore-scripts
COPY apps/ui ./
RUN npm run build

FROM ghcr.io/astral-sh/uv:0.8-python3.13-bookworm-slim AS builder
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=0
WORKDIR /app
# `uv sync --frozen` needs the pyproject.toml of every workspace member, not only the ones
# this image installs.
COPY pyproject.toml uv.lock ./
COPY packages/contracts/pyproject.toml packages/contracts/
COPY packages/core/pyproject.toml packages/core/
COPY packages/engine/pyproject.toml packages/engine/
COPY packages/http/pyproject.toml packages/http/
COPY packages/runtime/pyproject.toml packages/runtime/
COPY apps/api/pyproject.toml apps/api/
COPY apps/controller/pyproject.toml apps/controller/
COPY apps/worker/pyproject.toml apps/worker/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-build --no-install-workspace --package meowly-api
COPY packages/contracts packages/contracts
COPY packages/runtime packages/runtime
# packages/core also ships the Alembic migrations (alembic.ini + alembic/), run from this image.
COPY packages/core packages/core
COPY packages/http packages/http
COPY apps/api apps/api
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --package meowly-api

FROM python:3.13-slim-bookworm
RUN useradd --no-create-home --uid 10001 app
WORKDIR /app
COPY --from=builder --chown=app:app /app /app
COPY --from=ui /ui/dist /app/ui
# ALEMBIC_CONFIG: a plain `alembic upgrade head` (the chart's `migrate` init container, compose)
# finds the migrations, which live with the models in packages/core (next to the package, in
# src/meowly_core, so they are importable and shipped together).
ENV PATH="/app/.venv/bin:$PATH" PYTHONUNBUFFERED=1 MEOWLY_UI_DIR=/app/ui \
    ALEMBIC_CONFIG=/app/packages/core/alembic.ini
# Numeric UID so Kubernetes' runAsNonRoot can verify it (matches useradd above).
USER 10001:10001
EXPOSE 8000
CMD ["meowly-api"]
