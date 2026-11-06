# Local development of meowly (see compose.yaml for what `make up` runs and its limits).
#
#   make up        the catalog in Docker: UI and API on http://localhost:8000 (API under /v1)
#   make ui        the UI from this checkout with hot reload (Vite on :5173) against that API
#   make check     every quality check; run it before opening a PR
#
#   make minikube-start   start the local cluster (minikube, Docker driver)
#   make minikube-dev     skaffold dev: the whole platform in the `meowly` namespace, with the
#                         PlatformTask CRD and the controller, port-forwarded to :8000
#   make minikube-delete  skaffold delete + the PVC it leaves behind (Postgres)

.DEFAULT_GOAL := help
.PHONY: help up down logs ps ui ui-install check check-python check-ui check-openapi check-helm \
	check-migrations minikube-start minikube-dev minikube-run minikube-delete minikube-pg-password

API_URL ?= http://localhost:8000
UI_PORT ?= 5173

help: ## List the targets
	@grep -hE '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  make %-18s %s\n", $$1, $$2}'

# ---- Local, no Kubernetes ----

up: ## Postgres + API (which serves the built UI), rebuilt from this checkout
	docker compose up -d --build --wait
	@echo "UI  $(API_URL)"
	@echo "API $(API_URL)/v1/docs"

down: ## Stop everything (keeps the database volume; `docker compose down -v` wipes it)
	docker compose down

logs: ## Follow the compose logs
	docker compose logs -f

ps: ## Compose services and their state
	docker compose ps

ui-install: ## Install the UI dependencies (npm ci)
	cd apps/ui && npm ci

ui: ## UI with hot reload on http://localhost:5173 (UI_PORT=...); Vite proxies /v1 to the compose API
	@curl -fsS -o /dev/null $(API_URL)/healthz/ready || { \
		echo "API not answering on $(API_URL): run 'make up' first"; exit 1; }
	@test -d apps/ui/node_modules || $(MAKE) ui-install
	cd apps/ui && API_URL=$(API_URL) npx vite --port $(UI_PORT) --strictPort

# ---- Local cluster (minikube + skaffold.yaml; no ingress, no cert-manager) ----
# Every kubectl call names the minikube context: the current one may be a real cluster.

MINIKUBE_CPUS ?= 4
MINIKUBE_MEMORY ?= 4g
KUBE_LOCAL = kubectl --context minikube -n meowly
LOCAL_PVCS = data-meowly-postgresql-0

minikube-start: ## Start minikube (Docker driver; MINIKUBE_CPUS=4, MINIKUBE_MEMORY=4g)
	minikube start --driver=docker --cpus=$(MINIKUBE_CPUS) --memory=$(MINIKUBE_MEMORY)

minikube-dev: ## skaffold dev on minikube: build, deploy, port-forward (:8000 UI/API, :5432 Postgres) and logs
	skaffold dev

minikube-run: ## skaffold run on minikube (deploy without watch, no port-forward)
	skaffold run

minikube-delete: ## skaffold delete + the PVC it leaves behind (the Postgres data is lost)
	skaffold delete
	$(KUBE_LOCAL) delete pvc $(LOCAL_PVCS) --ignore-not-found

minikube-pg-password: ## Password of the local Postgres (user meowly, localhost:5432)
	@$(KUBE_LOCAL) get secret meowly-postgresql -o jsonpath='{.data.password}' | base64 -d; echo

# ---- Quality checks ----

check: check-python check-ui check-openapi check-helm ## Every quality check (check-migrations needs Docker: run it apart)

check-python: ## ruff lint + format check, pyright, import boundaries (import-linter), pytest
	uv sync --all-packages --frozen
	uv run ruff check .
	uv run ruff format --check .
	uv run pyright
	uv run lint-imports
	uv run pytest -n auto

check-ui: ## UI eslint, tsc, vitest and prettier
	@test -d apps/ui/node_modules || $(MAKE) ui-install
	cd apps/ui && npm run lint && npm run typecheck && npm test && npx prettier --check src

check-openapi: ## apps/ui/src/api/schema.d.ts matches this checkout's API (fix: cd apps/ui && npm run generate-api:local)
	@test -d apps/ui/node_modules || $(MAKE) ui-install
	uv run --package meowly-api python -m meowly_api.openapi > apps/ui/openapi.json
	cd apps/ui && npm run -s check-api; status=$$?; rm -f openapi.json; exit $$status

CHART = deploy/charts/meowly

check-helm: ## helm lint + template of the chart: defaults and the minikube overlay
	helm lint $(CHART)
	helm lint $(CHART) -f deploy/values/minikube.yaml
	helm template --kube-version 1.30.0 meowly $(CHART) -n meowly > /dev/null
	helm template --kube-version 1.30.0 meowly $(CHART) -n meowly -f deploy/values/minikube.yaml > /dev/null
	helm template --kube-version 1.30.0 meowly $(CHART) -n meowly \
		--set postgresql.enabled=false --set api.database.existingSecret=meowly-database > /dev/null
	@# No bundled Postgres and no database configured: the chart must refuse to render.
	@if helm template --kube-version 1.30.0 meowly $(CHART) -n meowly \
		--set postgresql.enabled=false > /dev/null 2>&1; then \
		echo "check-helm: the chart rendered without any database configured"; exit 1; fi

PG_CHECK_PORT ?= 55432

check-migrations: ## alembic upgrade head + alembic check (packages/core) against a throwaway Postgres (Docker, port PG_CHECK_PORT)
	@docker rm -f meowly-check-postgres >/dev/null 2>&1 || true
	docker run -d --rm --name meowly-check-postgres -p $(PG_CHECK_PORT):5432 \
		-e POSTGRES_USER=meowly -e POSTGRES_PASSWORD=meowly -e POSTGRES_DB=meowly postgres:16-alpine >/dev/null
	@until docker exec meowly-check-postgres pg_isready -h 127.0.0.1 -U meowly -d meowly -q; do sleep 1; done
	cd packages/core && export MEOWLY_DATABASE_URL=postgresql+asyncpg://meowly:meowly@localhost:$(PG_CHECK_PORT)/meowly \
		&& uv run --extra migrations alembic upgrade head && uv run --extra migrations alembic check; \
		status=$$?; docker rm -f meowly-check-postgres >/dev/null; exit $$status
