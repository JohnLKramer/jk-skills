import { http, HttpResponse } from "msw";
import { setupServer } from "msw/node";
import { afterAll, afterEach, beforeAll, describe, expect, it, vi } from "vitest";
import { z } from "zod";

vi.mock("./env", () => ({ env: { BACKEND_URL: "http://backend.test" } }));

import { ApiError, apiGet } from "./api-client";

const server = setupServer();
beforeAll(() => {
  server.listen({ onUnhandledFrame: "error" });
});
afterEach(() => {
  server.resetHandlers();
});
afterAll(() => {
  server.close();
});

describe("apiGet", () => {
  it("returns parsed data", async () => {
    server.use(http.get("http://backend.test/ping", () => HttpResponse.json({ ok: true })));
    await expect(apiGet("/ping", z.object({ ok: z.boolean() }))).resolves.toEqual({ ok: true });
  });

  it("throws ApiError when the backend response violates the schema", async () => {
    server.use(http.get("http://backend.test/ping", () => HttpResponse.json({ ok: "yes" })));
    await expect(apiGet("/ping", z.object({ ok: z.boolean() }))).rejects.toBeInstanceOf(ApiError);
  });
});
