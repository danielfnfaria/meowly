# purr — monorepo do purr

**Internal Developer Platform.** O catálogo do que existe (componentes, times, templates,
ambientes) numa interface administrativa, e o autosserviço sobre ele: cada pedido de um
desenvolvedor — criar um serviço a partir de um template, provisionar um recurso, rodar uma
ação de plataforma — vira um objeto Kubernetes (`PlatformTask`) orquestrado por um controller
próprio, ao estilo Tekton: **o CR é a execução, o pod do worker é o seu log**.

O produto é composto por:

| App | Onde | Stack |
|---|---|---|
| `purr-api` | `apps/api` | FastAPI: API do catálogo, criação e leitura de tasks, e serve a UI |
| `purr-ui` | `apps/ui` | React 19 + Vite + Mantine, buildada no Dockerfile da API e servida por ela |
| `purr-controller` | `apps/controller` | Operator `kopf` + `lightkube`: reconcilia `PlatformTask` → `Job` e escreve o status |
| `purr-worker` | `apps/worker` | Só o processo do pod: executa a spec e escreve os eventos (JSONL) no stdout |

## Princípio arquitetural: duas fontes de verdade, nenhuma duplicada

**Postgres é a fonte de verdade do catálogo; Kubernetes, das execuções.** Nenhuma execução
vira linha de tabela e nenhum item de catálogo vive no cluster. O que a UI mostra é o que
`kubectl -n purr get platformtasks` mostra, porque é o mesmo objeto (ADR 0002, ADR 0004).

A segunda regra que protege isso: **o pod do worker não tem credencial de cluster nem de
banco**. Ele recebe uma spec imutável e reporta pelo seu log. Não consegue ler o catálogo,
não vê outras tasks e não se autoriza nada.

## Fluxo de execução

```
UI/curl → POST /v1/tasks (API)
            ├── valida o que a task aponta (componente/template existem?)
            ├── resolve uma TaskSpec imutável
            └── cria o CR PlatformTask                         [Kubernetes = execuções]
                   ↓ (kopf: on.create / on.resume)
             controller → Job (imagem purr-worker, SA sem permissões,
                               PURR_TASK_SPEC no env, ownerReference para o CR)
                   ↓
             pod do worker → purr_engine.execute(spec)
                               └── TaskEvent em JSONL no stdout (started/step/log/finished)
                   ↓ (kopf: on.event de Job)
             controller lê o log do pod → último evento FINISHED → status do CR
                   ↓
             API/UI leem o CR (nunca o banco)
```

`PURR_LAUNCHER=memory` troca o `TaskStore` do Kubernetes pelo de memória: a task fica
registrada como `pending` no processo da API e nada a executa. É assim que o `make up`
funciona sem cluster — suficiente para mexer no catálogo e na UI, nunca para testar execução.

## Estrutura do repositório

```
purr/
├── CLAUDE.md
├── pyproject.toml            # uv workspace root: ruff, pyright strict, pytest, coverage e import-linter compartilhados
├── uv.lock
├── Makefile                  # up/down/ui, check*, minikube-*
├── compose.yaml              # desenvolvimento sem Kubernetes: Postgres + API (que serve a UI)
├── skaffold.yaml             # minikube: build das três imagens direto no Docker do cluster + helm install do chart + port-forwards
├── apps/
│   ├── api/                  # purr-api: routers do catálogo e de tasks, composition root (api/deps.py), docs sob /v1, serviço da UI, openapi.py (gera o cliente da UI)
│   ├── ui/                   # purr-ui: React/Vite/Mantine; cliente gerado do OpenAPI (src/api/schema.d.ts); fora do workspace uv
│   ├── controller/           # purr-controller: handlers kopf (task/job/timer) finos sobre services/ (job.py: manifest do Job; reconcile.py: a lógica pura), ports/kube.py + adapters (lightkube, memória)
│   └── worker/               # purr-worker: main.py, pod.py, settings.py — o motor vem de packages/engine
├── packages/
│   ├── contracts/            # purr-contracts: o fio entre os três processos — TaskSpec/TaskStatus (task.py), TaskEvent + JSONL (events.py), envelope do CR (platformtask.py), labels, enums, erros de domínio, SPEC_VERSION
│   ├── core/                 # purr-core: catálogo (models ORM + migrações Alembic, repositórios, services) e criação de tasks (ports/task_store.py + adapters Kubernetes/memória), composition.py (Core, build_core) e CoreSettings
│   ├── engine/               # purr-engine: executa uma task (engine.py: o laço spec → step → TaskStatus; steps.py: o registro por kind; events.py: o EventWriter)
│   ├── http/                 # purr-http: HTTP comum — app.py (build_app/run_server), errors.py (erro de domínio → status, um handler só), health.py, hardening.py (limite de corpo, access log, headers), bearer.py
│   └── runtime/              # purr-runtime: o comum de todo processo (folha: structlog + pydantic-settings) — configure_logging e ServerSettings/cached_settings
├── deploy/
│   ├── charts/purr/          # Helm chart único: CRD PlatformTask, API (+ init container migrate), controller com RBAC namespaced, SA do worker sem permissões, Postgres de dev, PDB opcional
│   └── values/minikube.yaml  # overlay que o skaffold aplica
└── docs/adr/                 # as decisões (0001–0004)
```

Cada app e cada pacote Python é um membro do workspace `uv` com `pyproject.toml`,
`src/<pacote>/` (com `py.typed`) e `tests/`; os apps têm também `Dockerfile` e um
`[project.scripts]`. Nomes: distribuição `purr-<nome>`, pacote Python `purr_<nome>`, imagem
`purr-<nome>`. `apps/ui` fica **fora** do workspace `uv` (ruff e pyright o ignoram) e tem o
seu `package.json`.

### Layout interno dos apps Python

```
src/<app>/
├── main.py           # entrypoint (app factory + run() / kopf / cli do worker)
├── settings.py       # pydantic-settings; toda config vem do ambiente, prefixo PURR_
├── api/              # routers FastAPI (só a API) — sem lógica de negócio
├── services/         # casos de uso; a decisão vive aqui, não no handler/router
├── ports/            # Protocols (TaskStore, Kube, ...)
└── adapters/         # implementações das portas (lightkube, memória, ...)
```

Regras: routers e handlers chamam services; services dependem de `Protocol`s (`ports/`), nunca
de adapters concretos; adapters entram por `Depends` (API) ou por construtor. A fiação
compartilhada vive **só** em `purr_core.composition` (`Core`, `build_core`, `build_task_store`),
usada pelo composition root de cada processo (`apps/api/src/purr_api/api/deps.py`). Services
não tocam em `session`: escrevem pelos repositórios.

## Fronteiras (travadas por import-linter, `uv run lint-imports`)

Camadas: `contracts` ← `core` ← `http` e `contracts` ← `engine`; `runtime` é folha. App nunca
importa app; pacote nunca importa app. O **controller** e o **worker** não importam `core` nem
`http` — as imagens deles não carregam SQLAlchemy, Alembic nem framework web. Detalhe e
motivo: ADR 0003.

## Domínio

| Entidade | O que é | Onde vive |
|---|---|---|
| `Owner` | Time dono de componentes (slug, nome, e-mail) | Postgres |
| `Component` | Serviço/peça do catálogo (slug, nome, time, repositório, sistema) | Postgres |
| `Template` | Fonte de scaffolding (repositório git + caminho + inputs) | Postgres |
| `Environment` | Ambiente onde um componente roda | Postgres |
| `PlatformTask` | **A execução**: `spec` (kind `noop`/`scaffold`/`provision`, componente, template, inputs, quem pediu) + `status` (fase, mensagem, outputs, timestamps) | Kubernetes (`platformtasks.purr.sh/v1alpha1`) |

O `PlatformTask` é podado pelo controller `controller.taskTtlSeconds` depois de terminar;
histórico além disso é um exportador futuro, nunca o Postgres.

## Stack e ferramentas

| Camada | Escolha |
|---|---|
| Python | 3.13, workspace `uv` |
| API | FastAPI, Pydantic v2, `pydantic-settings` |
| Banco | Postgres 16, SQLAlchemy 2.x async (`asyncpg`), Alembic |
| Operator | `kopf` + `lightkube` (async) |
| UI | React 19 + TypeScript (Vite), Mantine, TanStack Query; cliente gerado do OpenAPI da API |
| Qualidade | `ruff` (lint + format), `pyright` strict, `pytest` + `pytest-asyncio` + `httpx.AsyncClient`, `import-linter` (as fronteiras do ADR 0003) |
| Observabilidade | `structlog` JSON (o worker loga em stderr: o stdout é o stream de eventos) |
| Deploy | Helm chart único em `deploy/charts/purr`, Skaffold + overlay `deploy/values/<env>.yaml`, GitHub Actions |

## Comandos

```bash
# setup
uv sync --all-packages

# qualidade (rodar antes de qualquer commit/PR)
make check                 # python + ui + openapi + helm
make check-python          # ruff, pyright, lint-imports, pytest
make check-migrations      # alembic upgrade head + alembic check num Postgres descartável (Docker)

# desenvolvimento sem Kubernetes (só catálogo e UI; task fica pending)
make up                    # Postgres + API em http://localhost:8000 (docs em /v1/docs)
make ui                    # a UI deste checkout com hot reload em :5173 contra a API do compose
make down

# o produto inteiro, com execução de verdade
make minikube-start
make minikube-dev          # build das 3 imagens + chart + port-forward :8000
kubectl --context minikube -n purr get platformtasks

# contrato com a UI: toda mudança de API que afete a UI regenera o cliente no mesmo PR
cd apps/ui && npm run generate-api:local
```

## Convenções

- Código, comentários, docstrings, ADRs e mensagens de commit em **inglês**; `CLAUDE.md`,
  `README.md` e textos de UI em **pt-BR**.
- Commits em Conventional Commits (`feat(api): ...`, `fix(controller): ...`), pequenos.
- Tipagem completa (`pyright` strict); sem `Any` sem justificativa em comentário.
- `async` em todo I/O; nada bloqueante no event loop.
- Comentário explica o **porquê** (a consequência, o motivo da escolha), nunca o óbvio.
- Erros de domínio herdam de `purr_contracts.errors.PurrError` e são mapeados para HTTP num
  único lugar (`purr_http.errors`).
- Toda config vem do ambiente com prefixo `PURR_`; nada de arquivo de config no código.
- Toda mudança em `contracts` que altere `TaskSpec`/`TaskStatus`/`TaskEvent` incrementa
  `SPEC_VERSION` e mantém a leitura da versão anterior no worker por pelo menos uma release.
- Logs estruturados sempre com `task` quando houver; nunca logar payload de credencial.
- Migrações Alembic sempre revisadas à mão (`--autogenerate` é ponto de partida).
- Toda mudança de infra passa pelo chart ou pelo overlay; nada de `kubectl apply`/`edit` nem
  `helm --set` em ambiente compartilhado.
- Decisão de arquitetura relevante vira ADR em `docs/adr/`.

## Onde está o detalhe

| Guia | Conteúdo |
|---|---|
| `docs/adr/0001-single-helm-chart.md` | por que um chart só, e o que isso exige |
| `docs/adr/0002-tasks-live-in-kubernetes.md` | a task como CR, o worker sem credenciais, o log como resultado |
| `docs/adr/0003-apps-and-packages.md` | apps vs packages e as fronteiras de import |
| `docs/adr/0004-postgres-is-the-catalog.md` | o catálogo em Postgres, a API servindo a UI, o cliente gerado |
| `packages/contracts/CLAUDE.md` | o fio: specs, status, eventos, o envelope do CR e a regra de versão |
| `apps/ui/CLAUDE.md` | a UI e o contrato com o OpenAPI |
| `deploy/CLAUDE.md` | componentes do chart, RBAC, o guarda do banco, como acrescentar um componente |

## Estado atual (esqueleto)

O laço inteiro existe e roda, com um único step real: `noop`. `scaffold` e `provision` são
kinds declarados que levantam `UnavailableError` — a forma existe, o comportamento falso não.

Ainda **não** existe: autenticação (toda rota é aberta e `requested_by` é `"anonymous"`),
paginação e filtros no catálogo, import do catálogo a partir de YAML dos repositórios,
agendamento, e qualquer histórico de task além do TTL do CR.
