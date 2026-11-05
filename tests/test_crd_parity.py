"""The CRD and these models must describe the same thing.

The API server validates a PlatformTask against the chart's schema before any purr code sees
it, so a field added here and forgotten in the CRD is rejected at creation time — and one
removed here but left there is accepted and then ignored. Neither is visible in review unless
something checks, so this does (the rule is written down in `packages/contracts/CLAUDE.md`).
It lives in the root `tests/` because it crosses code and chart, like the other checks there.
"""

from pathlib import Path
from typing import Any

import pytest
import yaml

from purr_contracts import TaskKind, TaskPhase, TaskSpec, TaskStatus

CRD = Path(__file__).resolve().parents[1] / "deploy/charts/purr/templates/crds/platformtask.yaml"


def _properties() -> dict[str, Any]:
    if not CRD.is_file():
        pytest.skip("the chart is not in this tree (running against an installed wheel)")
    # The file is a Helm template: dropping its guard lines leaves plain YAML, which is all
    # this test needs (the guard only decides whether the CRD is rendered at all).
    body = "\n".join(
        line for line in CRD.read_text().splitlines() if not line.strip().startswith("{{")
    )
    doc: dict[str, Any] = yaml.safe_load(body)
    schema: dict[str, Any] = doc["spec"]["versions"][0]["schema"]["openAPIV3Schema"]["properties"]
    return schema


def test_the_crd_declares_every_spec_field() -> None:
    assert set(_properties()["spec"]["properties"]) == set(TaskSpec.model_fields)


def test_the_crd_declares_every_status_field() -> None:
    assert set(_properties()["status"]["properties"]) == set(TaskStatus.model_fields)


def test_the_crd_enums_match_the_python_enums() -> None:
    properties = _properties()
    assert properties["spec"]["properties"]["kind"]["enum"] == [k.value for k in TaskKind]
    assert properties["status"]["properties"]["phase"]["enum"] == [p.value for p in TaskPhase]


def test_the_crd_requires_what_a_task_cannot_be_created_without() -> None:
    # `kind` says what to run and `requested_by` is who asked: a task without either is not a
    # task. Everything else has a default in `TaskSpec`.
    assert set(_properties()["spec"]["required"]) == {"kind", "requested_by"}
