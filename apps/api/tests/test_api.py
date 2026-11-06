import httpx
from sqlalchemy.ext.asyncio import create_async_engine

from meowly_api.api.deps import AppState
from meowly_contracts import SPEC_VERSION
from meowly_core import Database


async def make_owner(client: httpx.AsyncClient, slug: str = "platform") -> str:
    response = await client.post("/v1/owners", json={"slug": slug, "name": "Platform"})
    assert response.status_code == 201
    return response.json()["id"]


def component_body(owner_id: str, slug: str = "billing") -> dict[str, str]:
    return {"slug": slug, "name": "Billing", "owner_id": owner_id}


async def test_ready_runs_select_1(client: httpx.AsyncClient) -> None:
    assert (await client.get("/healthz/live")).status_code == 200
    ready = await client.get("/healthz/ready")
    assert ready.status_code == 200
    assert ready.json() == {"status": "ok"}


async def test_ready_is_503_when_the_database_is_unreachable(
    client: httpx.AsyncClient, state: AppState
) -> None:
    state.db = Database(create_async_engine("sqlite+aiosqlite:////nonexistent-dir/meowly.db"))
    assert (await client.get("/healthz/ready")).status_code == 503
    assert (await client.get("/healthz/live")).status_code == 200


async def test_info(client: httpx.AsyncClient) -> None:
    body = (await client.get("/v1/info")).json()
    assert body["product"] == "meowly"
    assert body["spec_version"] == SPEC_VERSION
    assert body["api_version"]


async def test_component_crud(client: httpx.AsyncClient) -> None:
    owner_id = await make_owner(client)

    created = await client.post("/v1/components", json=component_body(owner_id))
    assert created.status_code == 201
    assert created.json()["slug"] == "billing"
    assert created.json()["owner_id"] == owner_id

    assert (await client.get("/v1/components/billing")).json()["name"] == "Billing"
    assert [c["slug"] for c in (await client.get("/v1/components")).json()] == ["billing"]

    updated = await client.patch(
        "/v1/components/billing", json={"name": "Billing v2", "system": "payments"}
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "Billing v2"
    assert updated.json()["system"] == "payments"
    assert updated.json()["owner_id"] == owner_id  # not sent, not touched

    assert (await client.delete("/v1/components/billing")).status_code == 204
    assert (await client.get("/v1/components/billing")).status_code == 404


async def test_duplicate_slug_is_409(client: httpx.AsyncClient) -> None:
    owner_id = await make_owner(client)
    assert (await client.post("/v1/components", json=component_body(owner_id))).status_code == 201
    again = await client.post("/v1/components", json=component_body(owner_id))
    assert again.status_code == 409
    assert set(again.json()) == {"code", "message"}


async def test_unknown_component_is_404(client: httpx.AsyncClient) -> None:
    response = await client.get("/v1/components/nope")
    assert response.status_code == 404
    assert set(response.json()) == {"code", "message"}


async def test_unknown_owner_is_404(client: httpx.AsyncClient) -> None:
    body = component_body("00000000-0000-0000-0000-000000000000")
    assert (await client.post("/v1/components", json=body)).status_code == 404


async def test_invalid_payload_is_422_in_the_error_format(client: httpx.AsyncClient) -> None:
    response = await client.post("/v1/components", json={"slug": "Not A Slug"})
    assert response.status_code == 422
    assert set(response.json()) == {"code", "message"}


async def test_null_on_a_required_field_is_422(client: httpx.AsyncClient) -> None:
    owner_id = await make_owner(client)
    await client.post("/v1/components", json=component_body(owner_id))
    response = await client.patch("/v1/components/billing", json={"name": None})
    assert response.status_code == 422


async def test_other_entities_round_trip(client: httpx.AsyncClient) -> None:
    template = {"slug": "svc", "name": "Service", "source_url": "https://x/y", "inputs": {"a": "b"}}
    assert (await client.post("/v1/templates", json=template)).json()["inputs"] == {"a": "b"}
    assert (await client.get("/v1/templates/svc")).status_code == 200
    env = await client.post("/v1/environments", json={"slug": "dev", "name": "Dev"})
    assert env.status_code == 201
    assert (await client.delete("/v1/environments/dev")).status_code == 204
    assert (await client.delete("/v1/templates/svc")).status_code == 204


async def test_create_and_read_a_task(client: httpx.AsyncClient) -> None:
    created = await client.post("/v1/tasks", json={"kind": "noop"})
    assert created.status_code == 201
    task = created.json()
    assert task["name"].startswith("task-")
    assert task["phase"] == "pending"
    assert task["kind"] == "noop"

    assert [t["name"] for t in (await client.get("/v1/tasks")).json()] == [task["name"]]
    assert (await client.get(f"/v1/tasks/{task['name']}")).json()["name"] == task["name"]
    assert (await client.get("/v1/tasks/task-unknown")).status_code == 404


EXPECTED_OPERATION_IDS = {
    "get_info",
    *(
        f"{verb}_{entity}"
        for verb in ("create", "get", "update", "delete")
        for entity in ("owner", "component", "template", "environment")
    ),
    *(f"list_{entity}" for entity in ("owners", "components", "templates", "environments")),
    "create_task",
    "list_tasks",
    "get_task",
}


async def test_openapi_is_served_with_explicit_operation_ids(client: httpx.AsyncClient) -> None:
    assert (await client.get("/v1/docs")).status_code == 200
    document = await client.get("/v1/openapi.json")
    assert document.status_code == 200

    # The UI's TypeScript client is generated from these names (ADR 0004): a route without an
    # explicit one gets a path-derived name (`..._v1_components_get`), and a rename breaks the
    # UI silently. Hence the exact set: adding or renaming a route means editing this test.
    operations = [
        (path, method, op)
        for path, item in document.json()["paths"].items()
        for method, op in item.items()
    ]
    assert operations
    missing = [(p, m) for p, m, op in operations if "operationId" not in op]
    assert not missing
    assert {op["operationId"] for _, _, op in operations} == EXPECTED_OPERATION_IDS
    assert len(operations) == len(EXPECTED_OPERATION_IDS)


async def test_the_error_body_is_in_the_schema_not_only_in_the_handler(
    client: httpx.AsyncClient,
) -> None:
    # The UI is generated from this document (ADR 0004). An error shape that only exists at
    # runtime forces the client to guess it, so every route declares `ErrorOut` and the 422
    # is ours, not FastAPI's `HTTPValidationError`.
    document = (await client.get("/v1/openapi.json")).json()
    assert document["components"]["schemas"]["ErrorOut"]["required"] == ["code", "message"]

    responses = document["paths"]["/v1/components/{slug}"]["get"]["responses"]
    for status_code in ("404", "409", "422", "502"):
        schema = responses[status_code]["content"]["application/json"]["schema"]
        assert schema["$ref"].endswith("/ErrorOut"), (status_code, schema)

    # And the runtime answer really has that shape.
    failed = await client.get("/v1/components/nope")
    assert failed.status_code == 404
    assert set(failed.json()) == {"code", "message"}


async def test_deleting_an_owner_with_components_answers_409(client: httpx.AsyncClient) -> None:
    owner_id = await make_owner(client)
    assert (await client.post("/v1/components", json=component_body(owner_id))).status_code == 201
    response = await client.delete("/v1/owners/platform")
    assert response.status_code == 409
    body = response.json()
    assert set(body) == {"code", "message"}
    assert "still referenced" in body["message"]
