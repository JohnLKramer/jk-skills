---
name: python-project-setup
description: >-
  Use when setting up a new Python project, scaffolding a src layout, adding
  or editing pyproject.toml, deciding on a Python client/server split, picking
  a build backend or dependency groups, writing a one-off PEP 723 script, or
  choosing whether a Python service needs a Dockerfile.
---

# Python Project Setup

## Overview

Standard structure and tooling for a modern Python project: `src/` layout, `pyproject.toml` with `hatchling` + PEP 735 dependency groups, `uv` + `ruff` + `mypy` as the toolchain, PEP 723 for one-off scripts, and contextual Docker guidance. Written for developers who aren't Python specialists — each rule below explains why, not just what.

## `src/` layout

Always use a `src/` layout, never a flat package at the repo root:

```text
my_project/
├── .python-version
├── pyproject.toml
├── uv.lock
├── src/
│   └── my_project/
│       ├── __init__.py
│       ├── main.py
│       └── cli.py
└── tests/
```

**Why:** without `src/`, running Python from the repo root puts the uncommitted working-tree package on `sys.path` ahead of the installed one. Tests and scripts then silently import your local edits even when you meant to test the installed package, masking packaging bugs until they hit production. The `src/` layout forces every import to go through the installed package, so dev and prod resolve imports the same way.

## `pyproject.toml`

Build backend is **hatchling**:

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

Dev dependencies go in **`[dependency-groups]`** (PEP 735), not `[project.optional-dependencies]`:

```toml
[dependency-groups]
dev = [
    "pytest>=8.0.0",
    "ruff>=0.3.0",
    "mypy>=1.8.0",
]
```

`[project.optional-dependencies]` is for extras end users can opt into (`pip install my-project[postgres]`); dev tooling isn't something a consumer of the package ever installs, so it belongs in a dependency group instead.

**Application vs. library dependency bounds:** an application (a service you deploy) only needs lower bounds — `fastapi>=0.110.0` — since you control exactly what gets installed via the lockfile. A **publishable library** should also pin upper bounds (`fastapi>=0.110.0,<1.0.0`) so it doesn't silently break downstream consumers on an unreviewed major bump.

**Single package vs. multi-package:**

- Default to a single package: client and server live as submodules of one `src/my_project/` when they share versioning and deploy together. Don't split until there's a reason to.
- Graduate to a **uv workspace** when the client needs to be installed or published independently, without pulling in server-only dependencies (FastAPI, SQLAlchemy, etc.):

```toml
# pyproject.toml at the workspace root
[tool.uv.workspace]
members = ["packages/*"]
```

```text
my_project/
├── pyproject.toml          # [tool.uv.workspace]
├── uv.lock                 # one shared lockfile for the whole workspace
└── packages/
    ├── my_project_client/
    │   ├── pyproject.toml
    │   └── src/my_project_client/
    └── my_project_server/
        ├── pyproject.toml
        └── src/my_project_server/
```

Each member is its own `pyproject.toml` + `src/` layout; the workspace root holds one shared `uv.lock` across all members.

## Toolchain

`uv` for environments and dependencies, `ruff` for formatting/linting, **and `mypy` as a required step** — not just a dependency group entry that never gets run:

```bash
uv sync                    # install deps into the project venv
uv add <package>           # add a runtime dependency
uv add --group dev <package>  # add a dev-only dependency
uv run ruff format         # format
uv run ruff check --fix    # lint, autofix
uv run mypy src/           # type-check — run this, don't just list it as a dep
```

## Script execution

Packaged, installable CLIs use `[project.scripts]`:

```toml
[project.scripts]
my-cli = "my_project.cli:main"
```

For a **one-off or throwaway script**, proactively suggest a PEP 723 inline-metadata script rather than adding it to the package — this is the default answer whenever a quick standalone script comes up, not a fallback:

```python
# /// script
# dependencies = [
#   "requests",
# ]
# ///

import requests

def main():
    print(requests.get("https://api.github.com").json())

if __name__ == "__main__":
    main()
```

Run with `uv run script.py` — `uv` reads the inline metadata and builds an ephemeral environment for it, no project install needed.

## Docker

Don't hardcode a blanket rule. Decide based on what the project actually is:

- **Has a server/service component** (FastAPI app, worker process, anything that runs as a long-lived process in production): include a Dockerfile using this pattern — multi-stage build, `uv sync --frozen`, `--compile-bytecode`, non-root user, `python:3.12-slim` runtime base.
- **Pure CLI tool** with no service component: skip the Dockerfile. It adds maintenance overhead with no deployment target that needs it.

```dockerfile
FROM python:3.12-slim AS build
RUN pip install uv
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --compile-bytecode --no-install-project
COPY src/ src/
RUN uv sync --frozen --compile-bytecode

FROM python:3.12-slim
RUN useradd --create-home appuser
WORKDIR /app
COPY --from=build /app/.venv .venv
COPY --from=build /app/src src
USER appuser
ENV PATH="/app/.venv/bin:$PATH"
CMD ["python", "-m", "my_project.main"]
```

## Bootstrap script

`scripts/bootstrap-python-env.sh` installs system-level tooling only — `uv` itself, and the pinned Python version from `.python-version` if `uv` doesn't already have it. It does **not** create any project directories or files; scaffolding decisions (single package vs. workspace, whether to add Docker, etc.) stay case-by-case and in your hands.

It's also symlinked as `bootstrap-python-env.sh` in `~/bin` (on `PATH`), so it can be run directly from any project directory without referencing this skill's path.

**Ask the user for confirmation before running this script.** It installs system-level tools (via a `curl | sh` installer and `uv python install`), so don't invoke it unprompted — confirm first, then run `bootstrap-python-env.sh` from the target project directory (or `bash scripts/bootstrap-python-env.sh` if running the copy inside this skill).

## Checklist

- [ ] `src/` layout, not a flat top-level package
- [ ] `pyproject.toml` uses hatchling as the build backend
- [ ] Dev deps in `[dependency-groups]`, not `[project.optional-dependencies]`
- [ ] Library deps pin upper bounds; application deps don't need to
- [ ] Single package by default; uv workspace only once independent client install/publish is needed
- [ ] `uv run mypy src/` is documented as a required command, not just a listed dependency
- [ ] One-off scripts get PEP 723 metadata suggested proactively, not just as a fallback
- [ ] Dockerfile included only if the project has a server/service component
- [ ] User confirmed before `bootstrap-python-env.sh` was run
