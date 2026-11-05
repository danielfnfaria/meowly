/// <reference types="vitest/config" />
import { fileURLToPath, URL } from "node:url";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// In dev the API is reached through a proxy so the browser stays same-origin (no CORS); in
// the image there is no proxy: the API serves the built UI itself (apps/api/.../api/ui.py).
export default defineConfig({
  plugins: [react()],
  resolve: { alias: { "@": fileURLToPath(new URL("./src", import.meta.url)) } },
  server: {
    port: 5173,
    proxy: {
      "/v1": { target: process.env.API_URL ?? "http://localhost:8000", changeOrigin: true },
    },
  },
  test: {
    environment: "happy-dom",
    globals: true,
    setupFiles: ["./vitest.setup.ts"],
    // Interaction tests are fast on a laptop but slow on a busy machine (e.g. `make check`
    // running everything in parallel); the 5 s default is too tight.
    testTimeout: 30_000,
    hookTimeout: 30_000,
  },
});
