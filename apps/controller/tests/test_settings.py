import json

import pytest

from purr_controller.settings import Settings


def _settings(monkeypatch: pytest.MonkeyPatch, resources: object) -> Settings:
    # Through the environment, as the chart sets it: the JSON parse happens before the
    # validator under test. `worker_image` is passed because it has no default.
    monkeypatch.setenv("PURR_WORKER_RESOURCES", json.dumps(resources))
    return Settings(worker_image="purr-worker:dev")


def test_a_numeric_quantity_is_accepted(monkeypatch: pytest.MonkeyPatch) -> None:
    # `cpu: 1` in values.yaml is valid YAML and valid Kubernetes; the controller must not
    # refuse to start over it.
    settings = _settings(monkeypatch, {"requests": {"cpu": 1, "memory": "128Mi"}})
    assert settings.worker_resources == {"requests": {"cpu": "1", "memory": "128Mi"}}


def test_no_resources_is_the_empty_default(monkeypatch: pytest.MonkeyPatch) -> None:
    assert _settings(monkeypatch, {}).worker_resources == {}
