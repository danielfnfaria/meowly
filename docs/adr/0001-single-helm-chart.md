# 0001: one Helm chart for the whole product

Status: accepted (2026-11-05).

## Context

purr is several processes that only make sense together: the API (which also serves the admin
UI), the `PlatformTask` controller, the CRD itself, the identity the worker Jobs run as and,
for development, a Postgres. They are versioned together in this monorepo and released
together.

The alternatives were a chart per component (API, controller, CRD) or raw manifests per
environment. Both push the same problem onto whoever installs purr: the CRD has to exist
before the controller starts, the controller has to know the image the worker Jobs use, and
the API has to point at the same namespace the controller watches. Split charts turn those
three facts into install-order documentation nobody reads.

## Decision

**One chart, `deploy/charts/purr`, holds every component**, each switchable by values. The
chart is the only way infrastructure changes: no `kubectl apply`, no `kubectl edit`, no
`helm --set` in a shared environment. Per-environment differences live in
`deploy/values/<env>.yaml` overlays, and `deploy/values/minikube.yaml` is the one `skaffold
dev` applies.

- `Chart.yaml`'s `version` goes up on any template or values change; `appVersion` is the
  default image tag of all three images.
- Every value is documented in `values.yaml` with what it does and what it costs.
- `helm lint` and `helm template` (defaults and every overlay) stay clean and run in
  `make check-helm` and in CI: a broken template fails before it reaches a cluster.
- The CRD ships as a regular template guarded by `crds.install`, not in Helm's `crds/`
  directory. Helm never templates nor upgrades files in `crds/`, and purr's CRD will change
  while the product is young; the cost is that uninstalling the release can take the CRD —
  and with it the task history — so `crds.install=false` exists for clusters where the CRD is
  managed apart.

## Consequences

- One `helm install` brings up a working platform; one `helm upgrade` moves every component
  to the same version.
- A component that must not run in an environment is turned off by a value, not by deleting
  manifests.
- The chart is reviewable: a diff in `deploy/` is the whole infrastructure change.
