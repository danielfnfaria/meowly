# 0002: a task is a Kubernetes object

Status: accepted (2026-11-05).

## Context

Everything purr does for a developer — scaffold a repository from a template, provision a
resource, run a platform action — is one execution with a lifecycle: requested, running,
succeeded or failed, with a log and a result. The obvious implementation is a `tasks` table
plus a queue plus a worker pool, and then a second implementation of the same lifecycle in
whatever runs the work.

That is exactly the drift purr wants to avoid: two places that both believe they know what a
task is, and a UI that shows one of them.

## Decision

**A task is a `PlatformTask` custom resource (`platformtasks.purr.sh/v1alpha1`), and nothing
about an execution is stored in Postgres.** The CR *is* the execution; the worker pod's log
*is* the task log. Tekton's model, scaled down.

1. The API resolves a request into an immutable `TaskSpec` and creates one `PlatformTask`.
   What the API resolved at creation time is what runs, even if the catalog changes a second
   later.
2. The controller (kopf) reconciles the CR into a `Job` with the worker image and writes the
   outcome onto the CR's `status` subresource. The controller is the only writer of status.
3. The worker process executes the spec it was given and prints `TaskEvent` lines (JSONL) on
   stdout — the pod's stdout carries nothing else, so its own logs go to stderr.
4. The API and the UI only ever read: `kubectl -n purr get platformtasks` and the UI show the
   same objects, because there is only one.
5. **The worker pod has no cluster credentials and no database credentials.** It receives its
   spec and reports through its log; it cannot read the catalog, cannot touch other tasks and
   cannot grant itself anything. Its ServiceAccount exists only to be nameable and holds no
   permissions.
6. A terminated `PlatformTask` is pruned by the controller after
   `controller.taskTtlSeconds`. History beyond that is a future exporter, never Postgres.

## Consequences

- No queue, no worker pool, no second lifecycle: Kubernetes schedules, retries and garbage
  collects.
- `kubectl get platformtasks` is a first-class debugging tool, and it agrees with the UI by
  construction.
- Running a task needs a cluster. `make up` (compose) starts the API with
  `PURR_LAUNCHER=memory`: tasks are recorded in the API process and nothing executes them,
  which is enough to work on the catalog and the UI. The full loop is `make minikube-dev`.
- The spec reaches the worker as an environment variable on the Job. That is fine while specs
  carry no credentials; the day a task needs one, it moves to a per-task Secret and this ADR
  gets an amendment.
- Changing `TaskSpec`, `TaskStatus` or `TaskEvent` bumps `SPEC_VERSION` in
  `packages/contracts`, and the worker keeps reading the previous version for at least one
  release: a task created before an upgrade still runs after it.
