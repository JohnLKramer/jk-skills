import { createEnv } from "@t3-oss/env-nextjs";
import { z } from "zod";

// The only file allowed to read process.env. A missing or malformed variable
// fails the build and the server start; there are no fallback values.
export const env = createEnv({
  server: {
    BACKEND_URL: z.url(),
  },
  client: {},
  runtimeEnv: {
    BACKEND_URL: process.env.BACKEND_URL,
  },
  emptyStringAsUndefined: true,
});
