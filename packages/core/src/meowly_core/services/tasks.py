import uuid

from meowly_contracts import COMPONENT_LABEL, TASK_LABEL, NotFoundError, PlatformTask, TaskSpec
from meowly_core.ports import TaskStore
from meowly_core.repositories import ComponentRepository, TemplateRepository


class TaskService:
    """Creating and reading tasks. The execution is a PlatformTask, never a row (ADR 0002),
    but what a task points at is catalog, so it is checked here."""

    def __init__(
        self,
        store: TaskStore,
        components: ComponentRepository,
        templates: TemplateRepository,
    ) -> None:
        self._store = store
        self._components = components
        self._templates = templates

    async def create(self, spec: TaskSpec) -> PlatformTask:
        # A spec is immutable once created and the worker cannot read the catalog (ADR 0002):
        # an unknown slug would only surface as a failed pod minutes later, with a worse
        # message. Here it is one query against the API's own database.
        await self._require_catalog(spec)
        name = f"task-{uuid.uuid4().hex[:10]}"
        # The labels are what the controller puts on the Job/Pod, so `kubectl get -l` finds
        # everything a task created.
        labels = {TASK_LABEL: name}
        if spec.component:
            labels[COMPONENT_LABEL] = spec.component
        return await self._store.create(spec, name=name, labels=labels)

    async def _require_catalog(self, spec: TaskSpec) -> None:
        if spec.component and await self._components.get_by_slug(spec.component) is None:
            raise NotFoundError(f"component {spec.component} not found")
        if spec.template and await self._templates.get_by_slug(spec.template) is None:
            raise NotFoundError(f"template {spec.template} not found")

    async def list(self) -> list[PlatformTask]:
        return await self._store.list()

    async def get(self, name: str) -> PlatformTask:
        return await self._store.get(name)
