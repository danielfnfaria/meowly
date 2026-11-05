import { MantineProvider } from "@mantine/core";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { vi } from "vitest";
import { App } from "@/App";

type Handler = (request: Request) => Response | Promise<Response>;

export const json = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json" } });

/** Stubs `fetch`: routes are keyed by "METHOD /path"; an unmapped call fails the test loudly. */
export function mockApi(routes: Record<string, Handler>) {
  const calls: Request[] = [];
  const fn = vi.fn((input: Request) => {
    calls.push(input);
    const key = `${input.method} ${new URL(input.url).pathname}`;
    const handler = routes[key];
    if (!handler) return Promise.resolve(json({ code: "unmocked", message: key }, 599));
    return Promise.resolve(handler(input));
  });
  vi.stubGlobal("fetch", fn);
  return calls;
}

export const INFO = json({ product: "purr", api_version: "1.2.3", spec_version: 1 });
export const info = () => INFO.clone();

export function renderApp(path = "/") {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <MantineProvider>
        <MemoryRouter initialEntries={[path]}>
          <App />
        </MemoryRouter>
      </MantineProvider>
    </QueryClientProvider>,
  );
}
