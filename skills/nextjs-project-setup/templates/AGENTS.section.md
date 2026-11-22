
## Project standards

- Run `mise run check` before saying work is done. Also run `mise run e2e` when a change touches routing, metadata, or Server Actions.
- The backend is called only from `src/features/*/api.ts` through `src/lib/api-client.ts`. A Client Component never imports `api.ts`; mutations go through Server Actions.
- Read configuration only through `src/lib/env.ts`. Do not call `fetch` or read `process.env` anywhere else.
- Do not edit `src/generated/`. Do not add `utils/` or `helpers/` directories, `any`, or `@ts-ignore`.
- A missing config value or a backend response that fails Zod validation is a loud error, not a fallback.
