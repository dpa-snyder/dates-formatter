#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

if [[ "${PROJECT_DEV_SHELL:-}" != "leading-zeros-dates" ]]; then
  echo "Enter this project's Nix shell first: nix develop" >&2
  exit 1
fi

venv="$PWD/.venv-nix"
if [[ ! -e "$venv" ]]; then
  uv venv --python "$DEV_SHELL_PYTHON" "$venv"
elif [[ ! -x "$venv/bin/python" ]]; then
  echo "Incomplete .venv-nix; move it aside, then rerun setup." >&2
  exit 1
fi

expected="$("$DEV_SHELL_PYTHON" -c 'import sys; print(sys.base_prefix)')"
actual="$("$venv/bin/python" -c 'import sys; print(sys.base_prefix)')"
if [[ "$actual" != "$expected" ]]; then
  echo "Nix Python changed; move .venv-nix aside, then rerun setup." >&2
  exit 1
fi

uv pip sync --python "$venv/bin/python" --require-hashes requirements-dev.lock

uv pip check --python "$venv/bin/python"
echo "Dependencies ready in .venv-nix; existing venv/.venv preserved."
