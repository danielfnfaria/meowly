import createClient from "openapi-fetch";
import type { components, paths } from "./schema";

// Same-origin: the API serves the UI build and the Vite dev proxy forwards /v1 to it. `fetch` is
// looked up per call so tests can stub `globalThis.fetch` after this module loads.
export const api = createClient<paths>({
  baseUrl: "/",
  fetch: (request) => globalThis.fetch(request),
});

type Schemas = components["schemas"];
export type Owner = Schemas["OwnerOut"];
export type Component = Schemas["ComponentOut"];
export type ComponentCreate = Schemas["ComponentCreate"];
export type Template = Schemas["TemplateOut"];
export type Environment = Schemas["EnvironmentOut"];
export type Task = Schemas["TaskOut"];
export type TaskCreate = Schemas["TaskCreate"];
export type TaskKind = Schemas["TaskKind"];
export type TaskPhase = Schemas["TaskPhase"];
export type Info = Schemas["InfoOut"];

/** Error returned by the API: domain errors are `{code, message}`, validation errors `{detail}`. */
export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly code: string,
    message: string,
  ) {
    super(message);
  }
}

interface ErrorBody {
  code?: string;
  message?: string;
  detail?: string | { msg: string; loc: (string | number)[] }[];
}

export function toApiError(status: number, body: unknown): ApiError {
  const err = (typeof body === "object" ? body : undefined) as ErrorBody | undefined;
  if (err?.message) return new ApiError(status, err.code ?? "error", err.message);
  if (typeof err?.detail === "string") return new ApiError(status, "error", err.detail);
  if (Array.isArray(err?.detail)) {
    const msg = err.detail.map((d) => `${d.loc.slice(1).join(".")}: ${d.msg}`).join("; ");
    return new ApiError(status, "validation_error", msg);
  }
  return new ApiError(status, "error", `Erro HTTP ${status}`);
}

/** Unwrap an openapi-fetch result into its data or a thrown ApiError. */
export function unwrap<T>(result: { data?: T; error?: unknown; response: Response }): T {
  if (result.error !== undefined || !result.response.ok) {
    throw toApiError(result.response.status, result.error);
  }
  return result.data as T;
}
