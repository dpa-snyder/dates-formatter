#!/bin/zsh

set -euo pipefail

if [[ "${PROJECT_DEV_SHELL:-}" == "leading-zeros-dates" ]]; then
  if [[ ! -x ".venv-nix/bin/python" ]]; then
    echo "Run bash scripts/setup-dev.sh inside the Nix shell first." >&2
    exit 1
  fi
  exec ./.venv-nix/bin/python -m unittest discover -s tests -q
fi

if [[ ! -x ".venv/bin/python" ]]; then
  python3 -m venv .venv
fi

if ! ./.venv/bin/python -c 'import importlib.util as u; mods=("pandas","openpyxl","customtkinter"); raise SystemExit(0 if all(u.find_spec(m) for m in mods) else 1)' >/dev/null 2>&1; then
  ./.venv/bin/python -m pip install -r requirements.txt
fi

./.venv/bin/python -m unittest discover -s tests -q
