#!/usr/bin/env bash
# Installs system-level Python tooling: uv, and the pinned Python version
# from .python-version (if present). Does not create any project files or
# directories. Idempotent: safe to re-run.
set -euo pipefail

if command -v uv >/dev/null 2>&1; then
  echo "uv already installed: $(uv --version)"
else
  echo "Installing uv..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
fi

if [ -f .python-version ]; then
  pinned_version="$(tr -d '[:space:]' < .python-version)"
  echo "Found .python-version: ${pinned_version}"
  if uv python list --only-installed 2>/dev/null | grep -q "${pinned_version}"; then
    echo "Python ${pinned_version} already installed via uv."
  else
    echo "Installing Python ${pinned_version} via uv..."
    uv python install "${pinned_version}"
  fi
else
  echo "No .python-version file found; skipping Python version install."
fi
