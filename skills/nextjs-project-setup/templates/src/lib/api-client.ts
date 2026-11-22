import "server-only";

import type { z } from "zod";

import { env } from "./env";

export class ApiError extends Error {
  constructor(
    readonly status: number,
    readonly path: string,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

/** GET a backend path and parse the body with the schema; a mismatch throws with the Zod issues. */
export async function apiGet<S extends z.ZodType>(path: string, schema: S): Promise<z.output<S>> {
  const response = await fetch(new URL(path, env.BACKEND_URL));
  if (!response.ok) {
    throw new ApiError(response.status, path, `GET ${path} returned ${String(response.status)}`);
  }
  const parsed = schema.safeParse(await response.json());
  if (!parsed.success) {
    throw new ApiError(502, path, `GET ${path} response failed validation: ${parsed.error.message}`);
  }
  return parsed.data;
}
