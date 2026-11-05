# deploy/ — o chart e os ambientes

Um chart único, `deploy/charts/purr`, com todo o produto (ADR 0001). Nada de `kubectl apply`,
`kubectl edit` ou `helm --set` em ambiente compartilhado: a mudança passa pelo chart (com bump
de `version` no `Chart.yaml`) ou pelo overlay em `deploy/values/`.

## Componentes

| Caminho | O que instala |
|---|---|
| `templates/crds/platformtask.yaml` | O CRD `platformtasks.purr.sh` (`v1alpha1`), com `status` como subrecurso e colunas PHASE/KIND/AGE. Guardado por `crds.install` |
| `templates/api/` | Deployment (com o init container `migrate` rodando `alembic upgrade head`), Service, ServiceAccount, Role/RoleBinding e o Secret da URL do banco |
| `templates/controller/` | Deployment de uma réplica (não serve HTTP, não tem Service), ServiceAccount e Role/RoleBinding |
| `templates/worker/serviceaccount.yaml` | A identidade dos Jobs, **sem nenhuma permissão** (ADR 0002) |
| `templates/postgresql/` | StatefulSet + Service + Secret, só para desenvolvimento (`postgresql.enabled`) |
| `templates/pdb.yaml` | PodDisruptionBudget opcional da API (nunca do controller nem do Postgres: um réplica única com PDB bloqueia drain de nó) |

## RBAC — o que cada identidade pode

Tudo *namespaced*; não existe ClusterRole no chart.

- **controller**: `platformtasks` (get/list/watch/create/patch/delete) + `platformtasks/status`
  (get/patch/update) + `jobs` (create/get/list/watch/delete) + `pods` e `pods/log`
  (get/list/watch) + `events` (create/patch). É o **único** escritor de status.
- **api**: cria e lê `platformtasks`, lê `pods`/`pods/log`. Não mexe em Job.
- **worker**: nada, e o Job sobe com `automountServiceAccountToken: false` — o pod não fala com
  o API server.

## O guarda do banco

Os defaults do chart são uma instalação que sobe sozinha: `postgresql.enabled: true` e a URL
apontando para o Service do Postgres de dev. Produção põe `postgresql.enabled: false` e
`api.database.existingSecret`. **Com o Postgres embutido desligado e nenhum banco configurado o
render falha de propósito** (`templates/api/secret.yaml`), em vez de instalar uma API que fica
em crash-loop contra um Service que não existe. `make check-helm` tem um caso negativo que trava
esse comportamento.

## Antes de commitar qualquer mudança aqui

```bash
make check-helm     # lint + template dos defaults, do overlay, do caso com Secret externo
                    # e a asserção de que o caso sem banco falha
```

## Acrescentar um componente ao chart

1. `templates/<componente>/` com Deployment (+ Service se servir HTTP), ServiceAccount e
   Role/RoleBinding com o **mínimo** de verbos.
2. Um bloco em `values.yaml` com `image.{repository,tag,pullPolicy}` e **todo valor comentado**
   com o que é e qual a consequência de mudá-lo.
3. Se a imagem é buildada localmente, acrescente-a a `skaffold.yaml` (artifact + os
   `setValueTemplates` do repository e da tag).
4. `version` do `Chart.yaml` +1, e `make check-helm`.

## Ambiente local

`skaffold dev` (via `make minikube-dev`) builda as três imagens direto no Docker do minikube
(sem registry, tag por conteúdo, então o `IfNotPresent` do chart usa o que acabou de sair),
instala o chart com `deploy/values/minikube.yaml` no namespace `purr` e faz port-forward da API
(:8000) e do Postgres (:5432). O `skaffold.yaml` **fixa `kubeContext: minikube`** de propósito:
o contexto atual pode ser um cluster de verdade. Sem ingress e sem cert-manager.
