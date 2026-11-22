---
name: nextjs-project-setup
description: >-
  Use when creating a new Next.js project, scaffolding a Next.js or React
  front end that calls a separate backend (BFF), pinning Node and pnpm with
  mise, or adding lint, typecheck, test, or git-hook tooling to a Next.js app.
---

# Next.js Project Setup

## Overview

`scripts/scaffold.sh` creates a Next.js 16 App Router project managed by mise
and wired to the rules in [standards.md](standards.md). Run the script; do not
re-derive its steps by hand. Every rule in the standards names its enforcing
tool, and the script installs and configures those tools.

## Scaffold

1. Confirm the target directory with the user. It must not exist or must be empty.
2. Run `bash scripts/scaffold.sh <target-dir>` (path relative to this skill).
   It installs Node and pnpm through mise, runs `create-next-app`, then adds
   typed ESLint, Prettier, dependency-cruiser, knip, Vitest, MSW, Playwright,
   axe, lefthook, Zod, and `@t3-oss/env-nextjs`.
3. Run `mise run check` in the new project. It must pass before you report done.
4. Tell the user the next steps the script cannot do for them:
   `pnpm exec playwright install chromium` before `mise run e2e`; `git init`
   then `pnpm exec lefthook install` if the project is not yet a repository;
   set the real `BACKEND_URL` in `.env.local`.

To scaffold without touching your real mise installs, set `MISE_DATA_DIR`,
`MISE_STATE_DIR`, and `MISE_CACHE_DIR` to a scratch directory first, and add
`$HOME/.config/mise` to `MISE_TRUSTED_CONFIG_PATHS` so mise can still read
your config.

## What you get

| Piece | Where |
|-------|-------|
| Node and pnpm pinned, one task per check | `mise.toml` (`mise run check`, `ci`, `e2e`, ...) |
| fetch only in `lib/api-client.ts`; `process.env` only in `lib/env.ts` | `eslint.config.mjs` |
| Layer, feature-isolation, and cycle rules | `.dependency-cruiser.cjs` |
| Strict `tsconfig` flags, `engines`, `packageManager` | patched by the script |
| Server-only API client with Zod parsing, with a sample MSW test | `src/lib/` |
| Agent instructions appended to the generated `AGENTS.md` | `AGENTS.md` |

## Gotchas

- `create-next-app` refuses a directory containing `mise.toml`. The script
  scaffolds first and writes `mise.toml` after. Do not write it earlier.
- Do not run `mise use -g`; the pin belongs in the project's `mise.toml`.
- `tsc` runs with no file arguments. Never pass staged files to it from a hook;
  that makes it ignore `tsconfig.json`.
- Both baselines without this skill pinned only Node, used npm, kept the
  default ESLint and `tsconfig`, and added no tests or boundary rules. Fixing
  those after the fact is the work this skill exists to avoid.
- MSW 3 renamed the option to `onUnhandledFrame`. If a template fails
  typecheck after a dependency bump, check the library's current types first.
- After changing a template, re-run the script in a scratch directory and run
  `mise run check` there. A green check on a fresh scaffold is the test.

## Editing the standards

`standards.md` is the source of truth. If you add a rule, add its enforcement
to a template and to the "What you get" table. A rule with no tool behind it is
marked **review** in the standards, so the gap stays visible.
