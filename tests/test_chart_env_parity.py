"""Every `MEOWLY_*` variable the chart injects into a process must be a field of that process's
`Settings`.

The Settings use `extra="ignore"`, so a variable that was renamed (or removed) in the code but
not in the chart is dropped silently and the default wins. This renders the chart and checks
each container's env against the right Settings class.

Needs the `helm` binary: the test is skipped when it is missing (the Python CI job does not
install it; the chart job covers rendering there).
"""

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest
import yaml
from pydantic_settings import BaseSettings

from meowly_api.settings import ServerSettings as ApiServerSettings
from meowly_api.settings import Settings as ApiSettings
from meowly_controller.settings import Settings as ControllerSettings

CHART = Path(__file__).resolve().parents[1] / "deploy/charts/meowly"
PREFIX = "MEOWLY_"


def _render() -> list[dict[str, Any]]:
    if shutil.which("helm") is None:
        pytest.skip("the helm binary is not installed")
    if not CHART.is_dir():
        pytest.skip("the chart is not in this tree")
    out = subprocess.run(
        ["helm", "template", "--kube-version", "1.30.0", "meowly", str(CHART), "-n", "meowly"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    return [doc for doc in yaml.safe_load_all(out) if isinstance(doc, dict)]  # pyright: ignore[reportUnknownVariableType]


def _fields(*settings: type[BaseSettings]) -> set[str]:
    return {name for cls in settings for name in cls.model_fields}


def _env(docs: list[dict[str, Any]], component: str) -> dict[str, dict[str, Any]]:
    """name -> env entry of every container (init containers included) of the Deployment."""
    (deployment,) = [
        d
        for d in docs
        if d.get("kind") == "Deployment" and d["metadata"]["name"].endswith(f"-{component}")
    ]
    pod = deployment["spec"]["template"]["spec"]
    env: dict[str, dict[str, Any]] = {}
    for container in [*pod.get("initContainers", []), *pod["containers"]]:
        for entry in container.get("env", []):
            env[entry["name"]] = entry
    return env


@pytest.mark.parametrize(
    ("component", "fields"),
    [
        ("api", _fields(ApiSettings, ApiServerSettings)),
        ("controller", _fields(ControllerSettings)),
    ],
)
def test_every_meowly_variable_the_chart_sets_is_a_settings_field(
    component: str, fields: set[str]
) -> None:
    env = _env(_render(), component)
    unknown = {
        name
        for name in env
        if name.startswith(PREFIX) and name.removeprefix(PREFIX).lower() not in fields
    }
    assert unknown == set()


def test_the_worker_resources_the_chart_renders_parse_into_the_controller_settings() -> None:
    entry = _env(_render(), "controller")["MEOWLY_WORKER_RESOURCES"]
    settings = ControllerSettings(worker_image="x", worker_resources=json.loads(entry["value"]))
    assert settings.worker_resources["limits"]["memory"]
