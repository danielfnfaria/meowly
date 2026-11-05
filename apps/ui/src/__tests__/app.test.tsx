import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { info, json, mockApi, renderApp } from "./helpers";
import type { Component, Owner, Task } from "@/api/client";

const stamp = "2026-11-05T12:00:00Z";
const owner: Owner = {
  id: "o1",
  slug: "platform",
  name: "Plataforma",
  email: null,
  created_at: stamp,
  updated_at: stamp,
};
const component: Component = {
  id: "c1",
  slug: "billing",
  name: "Billing API",
  owner_id: "o1",
  system: "payments",
  description: null,
  repo_url: null,
  created_at: stamp,
  updated_at: stamp,
};
const task: Task = {
  name: "noop-abc",
  kind: "noop",
  phase: "pending",
  message: null,
  component: "billing",
  template: null,
  requested_by: "anonymous",
  outputs: {},
  error: null,
  started_at: null,
  finished_at: null,
};

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("app", () => {
  it("renders the navigation and the API info in the footer", async () => {
    mockApi({
      "GET /v1/info": info,
      "GET /v1/components": () => json([]),
      "GET /v1/owners": () => json([]),
    });
    renderApp();
    const nav = screen.getByRole("navigation", { name: "Navegação principal" });
    for (const label of ["Catálogo", "Times", "Templates", "Ambientes", "Tasks"]) {
      expect(within(nav).getByText(label)).toBeInTheDocument();
    }
    expect(await screen.findByText(/API 1\.2\.3/)).toBeInTheDocument();
    expect(await screen.findByText("Nenhum componente cadastrado ainda.")).toBeInTheDocument();
  });

  it("lists the components the API returned", async () => {
    mockApi({
      "GET /v1/info": info,
      "GET /v1/components": () => json([component]),
      "GET /v1/owners": () => json([owner]),
    });
    renderApp();
    expect(await screen.findByText("billing")).toBeInTheDocument();
    expect(screen.getByText("Billing API")).toBeInTheDocument();
    expect(screen.getByText("payments")).toBeInTheDocument();
    expect((await screen.findAllByText("Plataforma")).length).toBeGreaterThan(0);
  });

  it("shows an error state when the API answers 500", async () => {
    mockApi({
      "GET /v1/info": info,
      "GET /v1/components": () =>
        json({ code: "internal_error", message: "banco fora do ar" }, 500),
      "GET /v1/owners": () => json([]),
    });
    renderApp();
    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent("banco fora do ar");
    expect(alert).toHaveTextContent("internal_error");
  });

  it("creates a task with POST /v1/tasks and the chosen body", async () => {
    const user = userEvent.setup();
    let created: unknown;
    const calls = mockApi({
      "GET /v1/info": info,
      "GET /v1/components": () => json([component]),
      "GET /v1/tasks": () => json([]),
      "POST /v1/tasks": async (req) => {
        created = await req.clone().json();
        return json(task, 201);
      },
    });
    renderApp("/tasks");
    expect(await screen.findByText(/a task\s+fica/)).toBeInTheDocument();
    await user.click((await screen.findAllByLabelText(/Componente/))[0] as HTMLElement);
    await user.click(await screen.findByRole("option", { name: "Billing API", hidden: true }));
    await user.click(screen.getByRole("button", { name: "Criar task" }));
    await waitFor(() => {
      expect(calls.some((c) => c.method === "POST")).toBe(true);
    });
    expect(created).toEqual({ kind: "noop", component: "billing" });
  });
});
