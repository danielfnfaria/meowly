# 0004: Postgres is the catalog, and the API serves the UI

Status: accepted (2026-11-05).

## Context

Two questions a platform has to answer early: where does the catalog (components, owners,
templates, environments) live, and how does the admin interface reach it?

Backstage-style IDPs often keep the catalog in YAML inside each repository and reconcile it
into memory. That is attractive — the catalog follows the code — but it makes every read
depend on a sync loop, and meowly's first need is plain CRUD over a handful of entities that a
human edits in a form.

For the UI, the alternatives were a separately deployed frontend (its own image, its own
ingress, CORS between the two) or the Grafana/Airflow arrangement: the API serves the built
assets on the same origin.

## Decision

1. **Postgres is the source of truth of the catalog**: `Owner`, `Component`, `Template`,
   `Environment`, with the ORM models, the repositories and the Alembic migrations together in
   `packages/core`. Kubernetes is the source of truth of executions (ADR 0002). Those are the
   only two stores, and neither duplicates the other.
2. **Migrations ship with the models** (`packages/core/alembic.ini` + `alembic/`), with
   Alembic as the optional `migrations` extra: only the API image installs it, because the
   API image is what runs them — as the chart's `migrate` init container, and as
   `alembic upgrade head` before the process in compose. They are always reviewed by hand;
   `--autogenerate` is a starting point.
3. **The API serves the UI**: `apps/ui` is built inside `apps/api/Dockerfile` with Node and
   copied in as static files (no Node in the final image); the API serves them on `/` and its
   own routes under `/v1`. Same origin, so no CORS, one ingress, one image to deploy.
4. **The UI talks to the API only through the generated OpenAPI client**
   (`apps/ui/src/api/schema.d.ts`). The API therefore owes the UI a stable OpenAPI with
   readable `operationId`s, and **any API change that affects the UI regenerates the client in
   the same PR** — `make check-openapi` fails otherwise.
5. Importing the catalog from repository YAML is not excluded; it would be a loader on top of
   these tables, not a replacement for them.

## Consequences

- Catalog reads are a SQL query: no sync loop, no eventual consistency, and a form can write.
- One image and one URL for the whole admin surface; the UI is never deployed on its own.
- The generated client turns an incompatible API change into a failing check instead of a
  runtime 422 in the browser.
- The API image is heavier (it carries the built UI and Alembic) and a UI-only change still
  rebuilds it. Accepted: one deployable is worth more than a thin image here.
