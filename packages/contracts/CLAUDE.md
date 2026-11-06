# packages/contracts — o fio entre os processos

`meowly_contracts` é o que a API, o controller e o worker combinam entre si. **Não importa nenhum
outro pacote do workspace** (import-linter trava isso): é a camada que todos podem depender sem
arrastar banco, HTTP nem cliente de Kubernetes.

| Módulo | O que define |
|---|---|
| `task.py` | `TaskSpec` (o pedido resolvido: kind, componente, template, inputs, quem pediu, trace) e `TaskStatus` (fase, mensagem, outputs, erro, timestamps) |
| `enums.py` | `TaskKind` (`noop`, `scaffold`, `provision`) e `TaskPhase`, com `phase.terminal` |
| `events.py` | `TaskEvent` + `encode_event`/`decode_event` (o JSONL do pod) e a convenção do evento final: `finished_data`/`status_from_event` |
| `platformtask.py` | O envelope do CR: `GROUP`/`VERSION`/`KIND`/`PLURAL`, `PlatformTask`, `task_body` (o que a API cria) e `task_from_body` (o que o controller lê) |
| `labels.py` | As labels que meowly põe no que cria (`meowly.dev/task`, `meowly.dev/component`, `managed-by`) |
| `errors.py` | Os erros de domínio (`MeowlyError` e filhos); `meowly_http.errors` é o único lugar que os mapeia para HTTP |
| `version.py` | `SPEC_VERSION` |

## Regras

1. **Toda mudança em `TaskSpec`, `TaskStatus` ou `TaskEvent` incrementa `SPEC_VERSION`** e o
   worker continua lendo a versão anterior por pelo menos uma release: uma task criada antes de
   um upgrade ainda é executada depois dele.
2. **Campo novo nasce opcional, com default.** Os modelos são `extra="forbid"`: um campo que
   um lado manda e o outro não conhece é erro de validação, não um valor ignorado em silêncio.
   Isso é deliberado (erro cedo e explícito), e é o que torna a regra 1 obrigatória.
3. **Convenção fica aqui, não nas duas pontas.** O status final viaja no `data` do evento
   `FINISHED`; o worker o escreve com `finished_data` e o controller o lê com
   `status_from_event`, porque nenhum dos dois pode importar o pacote do outro (ADR 0003). Se
   você se vir copiando uma string literal de um lado ao outro da fronteira, ela deveria ser
   uma função daqui.
4. **`decode_event` nunca levanta.** O stdout de um pod pode conter qualquer coisa que uma
   dependência decidiu imprimir; um leitor ignora o que não reconhece em vez de falhar a task.
5. O CRD em `deploy/charts/meowly/templates/crds/platformtask.yaml` descreve estes mesmos campos
   em `snake_case`. **Mudou um campo aqui, mude lá no mesmo PR** — o schema do CRD é a validação
   que o API server aplica antes de qualquer código nosso rodar.
