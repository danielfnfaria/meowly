"""What handlers share (carried in kopf's `memo`) and the operator's startup."""

from dataclasses import dataclass

import kopf
from lightkube import AsyncClient

from meowly_controller.adapters.lightkube import LightkubeKube
from meowly_controller.ports import Kube
from meowly_controller.settings import Settings, get_settings


@dataclass(frozen=True, slots=True)
class Runtime:
    settings: Settings
    kube: Kube


def runtime_of(memo: kopf.Memo) -> Runtime:
    """The `Runtime` the startup handler (or a test) put in the memo."""
    runtime: object = memo.get("runtime")
    if not isinstance(runtime, Runtime):
        raise kopf.PermanentError("controller runtime is not configured")
    return runtime


async def configure(memo: kopf.Memo, **_: object) -> None:
    cfg = get_settings()
    client = AsyncClient(namespace=cfg.execution_namespace)
    memo["runtime"] = Runtime(settings=cfg, kube=LightkubeKube(client, cfg.execution_namespace))
    memo["client"] = client


async def close(memo: kopf.Memo, **_: object) -> None:
    client: object = memo.get("client")
    if isinstance(client, AsyncClient):
        await client.close()
