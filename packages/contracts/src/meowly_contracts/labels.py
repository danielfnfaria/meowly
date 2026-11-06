"""Labels meowly puts on the objects it creates, and the one annotation it reads back."""

from typing import Final

from meowly_contracts.platformtask import GROUP

TASK_LABEL: Final = f"{GROUP}/task"
"""Name of the PlatformTask a Job/Pod belongs to."""

COMPONENT_LABEL: Final = f"{GROUP}/component"
"""Slug of the catalog component a task acts on, when it acts on one."""

MANAGED_BY_LABEL: Final = "app.kubernetes.io/managed-by"
MANAGED_BY: Final = "meowly-controller"
