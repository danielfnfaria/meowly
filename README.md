# meowly

**meowly** é uma *Internal Developer Platform*: o catálogo do que a engenharia tem — componentes,
times, templates e ambientes — numa interface administrativa, e o autosserviço sobre esse
catálogo. Cada pedido (criar um serviço a partir de um template, provisionar um recurso, rodar
uma ação de plataforma) vira um objeto Kubernetes, executado num pod isolado e acompanhado pela
UI ou pelo `kubectl`.

Para as decisões de arquitetura e as convenções de código, veja [`CLAUDE.md`](CLAUDE.md) e os
ADRs em [`docs/adr/`](docs/adr).

## O que tem aqui

| Pacote | Papel |
|---|---|
| `apps/api` | API FastAPI: catálogo (times, componentes, templates, ambientes), criação e leitura de tasks, OpenAPI sob `/v1` e o serviço da UI |
| `apps/ui` | Interface administrativa (React 19 + Mantine), buildada na imagem da API e servida por ela na mesma origem; só fala com a API pelo cliente gerado do OpenAPI |
| `apps/controller` | Operator `kopf`: reconcilia `PlatformTask` → `Job` com a imagem do worker e grava no status o resultado lido do log do pod |
| `apps/worker` | Processo do pod de execução: executa a spec que recebeu com `packages/engine` e escreve os eventos (JSONL) no stdout |
| `packages/contracts` | O fio entre os três processos: `TaskSpec`, `TaskStatus`, `TaskEvent`, o envelope do CR, as labels e os erros de domínio |
| `packages/core` | Catálogo (models ORM, migrações Alembic, repositórios, casos de uso) e criação de tasks (`TaskStore` com adapters de Kubernetes e de memória) |
| `packages/engine` | O motor que roda uma task: um step por `kind`, emitindo eventos |
| `packages/http` | HTTP comum: skeleton do app, erros → status, health, limite de corpo, access log |
| `packages/runtime` | O comum de todo processo: logging JSON e as settings de bind do servidor |
| `deploy/` | Helm chart único (`deploy/charts/meowly`: CRD `PlatformTask`, API, controller, identidade do worker e Postgres de dev) e o overlay do minikube |

**Postgres é a fonte de verdade do catálogo; Kubernetes, das execuções.** Nenhuma execução vira
linha de tabela (ADR 0002) e nenhum item de catálogo vive no cluster (ADR 0004).

## Pré-requisitos

- Python 3.13 e [`uv`](https://docs.astral.sh/uv/)
- Node >= 20.19 (a UI)
- Docker, para `make up`, `make check-migrations` e o build das imagens
- `kubectl`, `helm`, `skaffold` e `minikube` para o cluster local
  (`brew install kubectl helm skaffold minikube`)

## Rodando

### Sem Kubernetes (catálogo e UI)

```bash
make up          # Postgres + API em http://localhost:8000 (docs em /v1/docs)
make ui          # opcional: a UI deste checkout com hot reload em :5173
make down
```

Aqui a API sobe com `MEOWLY_LAUNCHER=memory`: criar uma task a registra como `pending` e **nada
a executa**. É o suficiente para trabalhar no catálogo e na interface.

### O produto inteiro, com execução de verdade

```bash
make minikube-start
make minikube-dev     # build das três imagens no Docker do minikube + helm install + port-forward :8000
```

O ciclo completo fica visível no cluster:

```bash
kubectl --context minikube -n meowly get platformtasks
kubectl --context minikube -n meowly logs job/<nome-da-task>
```

## Qualidade

```bash
make check               # tudo: python, ui, contrato do OpenAPI e chart
make check-python        # ruff, pyright strict, import-linter, pytest
make check-ui            # eslint, tsc, vitest, prettier
make check-openapi       # o cliente da UI está em dia com a API deste checkout?
make check-helm          # helm lint + template (defaults, overlay e o caso sem banco)
make check-migrations    # alembic upgrade head + alembic check num Postgres descartável
```

O mesmo roda no GitHub Actions (`.github/workflows/ci.yaml`), em três jobs: Python, Helm e UI.

## Estado atual

O laço completo funciona com um único step real, `noop`: a API cria o `PlatformTask`, o
controller cria o Job, o worker executa e reporta, o status volta ao CR. Os kinds `scaffold` e
`provision` estão declarados e recusam execução (`UnavailableError`) até serem implementados.

Não existe ainda: autenticação, paginação e filtros no catálogo, import do catálogo a partir de
YAML dos repositórios, agendamento e histórico de tasks além do TTL do CR.
