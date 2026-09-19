---
name: testing-system-altering-scripts
description: >-
  Use when verifying, testing, or running a script or tool that installs
  software, runs a curl-pipe-to-shell installer, modifies PATH or shell
  profiles/dotfiles, writes outside the project's own working directory, or
  otherwise changes state on the machine it runs on — before running it
  directly on the host.
---

# Testing System-Altering Scripts

## Overview

A script that installs a package, writes to `$HOME`, edits a dotfile, or touches anything outside the project directory leaves real state behind even when it "works". A clean exit code proves the script ran, not that it's safe to have run on this machine. Verify it in a throwaway container instead of the host.

## Rule

Before running a script or command to verify it, check whether it does any of:

- Runs a package manager or a `curl | sh` / `curl | bash` installer
- Writes into `$HOME` (dotfiles, `~/.local`, `~/.cargo`, `~/.config`, etc.) or any directory outside the project's own working tree
- Modifies `PATH`, shell rc files, or other persistent shell/environment state
- Installs or upgrades a system-level tool or language runtime

If any of those apply, run it inside a throwaway container, not on the host:

```bash
docker run --rm \
  -v "$(pwd)/scripts/install.sh:/install.sh:ro" \
  python:3.12-slim \
  bash -c "apt-get update -qq && apt-get install -y -qq curl >/dev/null && bash /install.sh"
```

- **Base image matches the target environment** — the image the script will actually run against in practice (e.g. `python:3.12-slim` for a Python bootstrap script), not an arbitrary one.
- **Mount only the artifact under test**, read-only (`:ro`), not the whole repo, unless the script needs more of it.
- **`--rm`** so the container is discarded after — never keep a named container around as a substitute for actually re-running the test.
- **Check results inside the container**, not just the exit code: did the expected files land, is the tool on `PATH`, does it print the right version.
- **Re-run the same command a second time in a fresh container** (or in the same one) to confirm the script is idempotent — a script that only works once is a script that breaks on every re-run in practice.

Skip the container only when there's no container runtime available, or the user explicitly asked for it to run on the host — and in that case, say so and confirm before running, rather than defaulting to the host silently.

Static analysis (`shellcheck script.sh`) is a fast, free complement — it catches quoting and logic bugs without executing anything — but it doesn't verify actual install behavior, so it doesn't replace running the script somewhere disposable.

## Examples

**Wrong** — runs directly on the real machine because the exit code is clean:

```bash
bash install-example-tool.sh
echo $?   # 0 — looks fine, but ~/.example-tool now exists on the real host
```

**Right** — same script, verified in a container that disappears afterward:

```bash
docker run --rm -v "$(pwd)/install-example-tool.sh:/install.sh:ro" ubuntu:22.04 \
  bash -c "bash /install.sh && test -f \$HOME/.example-tool/marker && echo OK"
# Real host's $HOME is untouched either way.
```

## Checklist

- [ ] Determined whether the script installs software, modifies PATH/dotfiles, or writes outside the project directory
- [ ] If yes, ran it inside a throwaway container (`--rm`), not directly on the host
- [ ] Base image matches the environment the script targets
- [ ] Only the artifact under test is mounted, not broader host state
- [ ] Verified idempotency by running the script twice
- [ ] If no container runtime was available, said so and got confirmation before running on the host
