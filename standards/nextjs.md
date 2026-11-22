# Next.js + TypeScript Project Standards

Standards for a Next.js (16.x, App Router) project that acts as a
backend-for-frontend (BFF) in front of separate backend services. Every rule
names what enforces it. A rule marked **review** has no tool behind it and
depends on a human or agent catching it.

Derived from `scratch/next_js_typescript_architectural_standards.md`, with the
errors corrected and the gaps filled. Facts about Next.js behavior were checked
against the Next 16 docs.

## 1. Architecture

Next.js is the presentation layer, the server-rendering engine, and the API
orchestrator. It never connects to a database.

```text
Server Component / Server Action
  -> features/<name>/api.ts        (typed, server-only, Zod-parsed)
  -> lib/api-client.ts             (base HTTP client, server-only)
  -> backend service

Client Component -> Server Action -> (same chain)
```

A Client Component never imports `api.ts`. Mutations from the browser go
through Server Actions. Client-side reads that need freshness (polling,
infinite scroll) go through a Route Handler that calls the same `api.ts`.

| Rule | Enforced by |
|------|-------------|
| `fetch()` only in `lib/api-client.ts` and Route Handlers for webhooks | ESLint `no-restricted-globals` for `fetch`, with an override that allows those files |
| `api.ts` and `api-client.ts` start with `import 'server-only'` | ESLint `no-restricted-syntax` on a missing import, plus `next build` failing on a client import |
| `'use client'` only on leaf components that need state, effects, or event handlers | **review** |
| Server Actions for UI-bound mutations; Route Handlers only for webhooks, OAuth callbacks, and streaming | **review** |
| Server-side GETs: `fetch` is memoized per render pass automatically; wrap non-`fetch` clients (gRPC, SDKs) in React `cache()` | **review** |

## 2. Directory structure

```text
src/
  app/            routing, layouts, metadata only; no business logic
  features/<name>/
    api.ts        server-only backend calls; parses with Zod
    schemas.ts    Zod schemas; types come from z.infer
    actions.ts    Server Actions for this feature
    components/
    hooks/        client hooks; never call api.ts
  components/     stateless UI primitives; imports nothing from features/
  lib/
    api-client.ts
    env.ts        the only file that reads process.env
    logger.ts
  generated/      OpenAPI output; never hand-edited
e2e/              Playwright
```

| Rule | Enforced by |
|------|-------------|
| `components/` does not import `features/` | `dependency-cruiser` |
| A feature does not import another feature's internals; cross-feature use goes through the other feature's `index.ts` | `dependency-cruiser` |
| `app/` holds no business logic: no imports from `lib/api-client` | `dependency-cruiser` |
| No circular dependencies | `dependency-cruiser` |
| No `utils/`, `helpers/`, or `misc/` directories; put code in the feature that owns it, or in `lib/` with a specific file name | **review** |
| No dead files, exports, or dependencies | `knip` |

## 3. Data contracts

Backend types come from the backend's OpenAPI spec, not from hand-written
interfaces.

- Generate types and Zod schemas into `src/generated/` (`openapi-typescript`
  for types, `orval` or `openapi-zod-client` for Zod). Commit the output so
  diffs show contract changes.
- `features/*/api.ts` parses every backend response with the Zod schema before
  returning it. A parse failure is a loud error with the endpoint and the Zod
  issue path in the log, not a fallback value.
- CI regenerates the client and fails if `git diff` is non-empty, which catches
  drift between the spec and the committed code.

## 4. SEO and crawlability

| Rule | Enforced by |
|------|-------------|
| Primary page content is fetched in a Server Component, not in `useEffect` or a client query hook | **review**; Playwright test that asserts the content is present with JavaScript disabled |
| Every dynamic route exports `generateMetadata` with title, description, OpenGraph, and canonical (`alternates.canonical`); root layout sets `metadataBase` | **review** |
| `app/sitemap.ts` and `app/robots.ts` exist | Playwright smoke test |
| JSON-LD is rendered in the Server Component for public entity pages | **review** |
| A missing entity returns 404 and a moved one returns a redirect, never a 200 "not found" message | Playwright status-code test |

Status codes and streaming: the status is fixed when the first byte is
flushed. A `loading.tsx` file or a `<Suspense>` boundary above the data fetch
starts the stream, so a later `notFound()` still returns 200 and only adds a
`noindex` tag. With Cache Components on, a request-time check inside the page
also stays at 200. To return a real 404 or redirect status, run the existence
check before streaming starts: in `proxy.ts`, or by fetching in the page
outside any Suspense boundary. A route that needs correct status codes does
not get a `loading.tsx`.

Redirects: `redirect()` sends 307 (303 for no-JavaScript form posts). Use
`permanentRedirect()` (308) when the backend says the move is permanent.

## 5. Caching

Next 16 does not cache `fetch` responses by default. Every data function
declares its caching intent.

- Opt in with Cache Components (`cacheComponents: true`) and the `'use cache'`
  directive with `cacheLife` and `cacheTag`.
- `revalidateTag(tag, profile)` takes a profile argument in 16; the one-argument
  form is deprecated. In a Server Action, use `updateTag` when the user must
  see their own write immediately.
- Anything reading `cookies()`, `headers()`, or `searchParams` is per-request.
  Keep it inside a `<Suspense>` boundary, away from cached content.
- `params`, `searchParams`, `cookies()`, and `headers()` are async-only in 16.
  Run `npx next typegen` for the `PageProps` and `LayoutProps` types.

Enforced by: **review**, plus `next build`, which fails on uncached data outside
Suspense once `cacheComponents` is on.

## 6. TypeScript

Required `tsconfig.json` flags:

```json
{
  "compilerOptions": {
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true,
    "noImplicitOverride": true,
    "verbatimModuleSyntax": true
  }
}
```

- `noUnusedLocals` and `noUnusedParameters` are left to ESLint, which has an
  autofix and an underscore-prefix escape. Do not enable both.
- `exactOptionalPropertyTypes` is opt-in. It breaks many React and library
  type definitions.
- `any` is banned by `@typescript-eslint/no-explicit-any`. `@ts-ignore` is
  banned. `@ts-expect-error` is allowed only with a description of at least 10
  characters (`ban-ts-comment`).

## 7. Security

| Rule | Enforced by |
|------|-------------|
| `process.env` is read only in `src/lib/env.ts`, validated with `@t3-oss/env-nextjs`, with server and `NEXT_PUBLIC_` variables split | ESLint `no-restricted-properties` on `process.env` outside `env.ts` |
| Every Server Action authenticates and authorizes the caller and parses its input with Zod. Actions are public POST endpoints. | **review**; vitest test per action for the unauthenticated case |
| `experimental.serverActions.allowedOrigins` is set when behind a proxy | **review** |
| Backend tokens and secrets never reach the client: sessions are httpOnly, Secure, SameSite cookies, and the BFF forwards credentials server-side | **review** |
| CSP with per-request nonce, plus `X-Content-Type-Options`, `Referrer-Policy`, and `frame-ancestors`, set in `proxy.ts` | Playwright test that asserts the headers |
| `NEXT_PUBLIC_` values are inlined at build time. For one image promoted across environments, serve environment-specific values from the server at runtime instead. | **review** |
| Dependency vulnerabilities | `pnpm audit --prod` or OSV-Scanner in CI; Renovate for updates |
| Committed secrets | `gitleaks` in CI and pre-commit |
| Code scanning | CodeQL in CI |
| Install scripts of dependencies | pnpm `onlyBuiltDependencies` allowlist and `minimumReleaseAge` |

## 8. Testing

| Tier | Tool | Covers |
|------|------|--------|
| Static | `tsc --noEmit` (no file arguments), ESLint, `knip`, `dependency-cruiser` | Contracts, boundaries, dead code |
| Unit | Vitest | Pure functions, Zod schemas, formatters |
| Component | Vitest + React Testing Library | Client components and hooks, and synchronous Server Components |
| BFF integration | Vitest + MSW (`msw/node`) | Server Actions, Route Handlers, `proxy.ts`, backend error to UI state mapping |
| End to end | Playwright + Dockerized backend | Happy paths and critical flows against the real stack |
| Accessibility | `@axe-core/playwright` on key pages; `eslint-plugin-jsx-a11y` (included in the Next config) | WCAG violations |

Limits that shape this table:

- Vitest cannot render `async` Server Components. Cover them in Playwright.
- Playwright's `page.route()` intercepts browser requests only. It cannot
  simulate a backend 500 seen by a Server Component or Server Action. For
  server-side failure cases, point the Next server at a fault-injecting proxy
  or WireMock, or register MSW in `instrumentation.ts` for a test-only run.
  Use `page.route()` only for requests the browser makes itself.

## 9. Observability and errors

- `instrumentation.ts` registers OpenTelemetry; traces and logs go to Datadog.
- `lib/logger.ts` emits structured JSON. Log values as fields, not in the
  message string.
- Each route segment with data has an `error.tsx`; the app has `global-error.tsx`.
- Backend errors are normalized in `api.ts` into a small typed error set. UI
  code never inspects raw backend responses.
- Misconfiguration (a missing env var, a Zod parse failure on a backend
  response) fails fast and loudly. No fallback values, no swallowed exceptions.

## 10. Accessibility and performance

- `next/image` and `next/font` for all images and fonts.
- `@next/bundle-analyzer` available as `ANALYZE=true pnpm build` (add the analyzer wrapper to `next.config.ts` when first needed).
- Lighthouse CI on key pages with budgets for LCP, CLS, and INP.

## 11. Tooling and enforcement

Pinned in `mise.toml`: Node (LTS, at least 20.9) and pnpm. `package.json`
carries `engines` and `packageManager`.

| Tool | Role |
|------|------|
| ESLint 9 flat config: `eslint-config-next/core-web-vitals`, `eslint-config-next/typescript`, `typescript-eslint` `strictTypeChecked` and `stylisticTypeChecked` with `projectService: true` | Lint. Typed rules are required: `no-floating-promises` and `no-misused-promises` do nothing without type information. |
| `eslint-plugin-simple-import-sort`, `consistent-type-imports` | Import order and `import type` |
| Prettier + `prettier-plugin-tailwindcss` | Formatting |
| `dependency-cruiser` | Layer, feature, and cycle rules |
| `knip` | Unused files, exports, and dependencies |
| Vitest, React Testing Library, MSW, Playwright, axe | Tests |
| lefthook | Pre-commit: Prettier and ESLint on staged files. Pre-push: typecheck. Hooks call mise tasks. |

`next lint` no longer exists in 16 and `next build` does not lint, so lint is
a separate task and a separate CI step.

Zero warnings: ESLint runs with `--max-warnings 0`.

### mise tasks

mise tasks are the single entry point. CI and the git hooks call the same
tasks, so a green local `mise run check` means a green CI.

| Task | Runs |
|------|------|
| `mise run lint` | ESLint, `--max-warnings 0` |
| `mise run format:check` | Prettier `--check` |
| `mise run typecheck` | `tsc --noEmit` |
| `mise run deps` | `dependency-cruiser` and `knip` |
| `mise run test` | Vitest |
| `mise run e2e` | Playwright |
| `mise run check` | lint, format:check, typecheck, deps, test |
| `mise run ci` | check, then `next build`, then e2e |

## 12. Instructions for AI agents

`AGENTS.md` at the repo root states, at minimum:

- Run `mise run check` before saying work is done. Run `mise run e2e` when the
  change touches routing, metadata, or Server Actions.
- Do not edit `src/generated/`; regenerate it with `mise run codegen`.
- Do not add `utils/` directories, `any`, `@ts-ignore`, or direct `fetch` and
  `process.env` use. The lint run will fail on them.
- Where a rule above says **review**, the agent is the reviewer.
