"""kopf handlers. Thin on purpose: they parse what kopf delivers, call `services/` for the
decision and act through the `Kube` port, so tests call them directly with `MemoryKube`.

They are plain functions and `register()` attaches them to kopf (called once by `main.run`;
tests never register). kopf's decorators would retype each handler as kopf's callback
protocol, which demands every kwarg kopf can pass, and break calling them directly.

kopf derives a handler's id from its `__qualname__` and keeps its progress in annotations
keyed by that id: the functions keep their names across modules.
"""

import kopf

from purr_contracts import GROUP, MANAGED_BY, MANAGED_BY_LABEL, PLURAL, TASK_LABEL, VERSION
from purr_controller.handlers.job import job_event
from purr_controller.handlers.runtime import Runtime, close, configure, runtime_of
from purr_controller.handlers.task import task_created
from purr_controller.handlers.timer import PRUNE_INTERVAL_SECONDS, task_timer


def register() -> None:
    """Attach the handlers to kopf's default registry."""
    kopf.on.startup()(configure)
    kopf.on.cleanup()(close)
    # `resume` as well as `create`: see `task_created`.
    kopf.on.create(GROUP, VERSION, PLURAL)(task_created)
    kopf.on.resume(GROUP, VERSION, PLURAL)(task_created)
    kopf.on.event(
        "batch", "v1", "jobs", labels={TASK_LABEL: kopf.PRESENT, MANAGED_BY_LABEL: MANAGED_BY}
    )(job_event)
    kopf.timer(GROUP, VERSION, PLURAL, interval=PRUNE_INTERVAL_SECONDS)(task_timer)


__all__ = [
    "Runtime",
    "close",
    "configure",
    "job_event",
    "register",
    "runtime_of",
    "task_created",
    "task_timer",
]
