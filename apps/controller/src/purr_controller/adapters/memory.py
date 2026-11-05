"""In-memory `Kube` for tests: records what the handlers do and lets a test stage the cluster."""

from purr_contracts import JsonDict, PlatformTask, TaskStatus


class MemoryKube:
    def __init__(self) -> None:
        self.jobs: dict[str, JsonDict] = {}
        self.logs: dict[str, str] = {}
        self.tasks: dict[str, PlatformTask] = {}
        self.status_patches: list[tuple[str, TaskStatus]] = []
        self.deleted_tasks: list[str] = []

    async def create_job(self, manifest: JsonDict) -> None:
        self.jobs.setdefault(manifest["metadata"]["name"], manifest)

    async def get_job(self, name: str) -> JsonDict | None:
        return self.jobs.get(name)

    async def pod_log(self, job_name: str) -> str:
        return self.logs.get(job_name, "")

    async def get_task(self, name: str) -> PlatformTask | None:
        return self.tasks.get(name)

    async def patch_task_status(self, name: str, status: TaskStatus) -> None:
        self.status_patches.append((name, status))
        task = self.tasks.get(name)
        if task is not None:
            self.tasks[name] = task.model_copy(update={"status": status})

    async def delete_task(self, name: str) -> None:
        self.deleted_tasks.append(name)
        self.tasks.pop(name, None)
