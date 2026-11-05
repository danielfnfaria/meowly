# Build context is the monorepo root (see skaffold.yaml).
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
    uv sync --frozen --no-dev --no-build --no-install-workspace --package purr-controller
COPY packages/contracts packages/contracts
COPY packages/runtime packages/runtime
COPY apps/controller apps/controller
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --package purr-controller

FROM python:3.13-slim-bookworm
RUN useradd --no-create-home --uid 10001 app
WORKDIR /app
COPY --from=builder --chown=app:app /app /app
ENV PATH="/app/.venv/bin:$PATH" PYTHONUNBUFFERED=1
# Numeric UID so Kubernetes' runAsNonRoot can verify it (matches useradd above).
USER 10001:10001
CMD ["purr-controller"]
