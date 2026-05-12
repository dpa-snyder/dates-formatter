# TODOs

Indexed task list. Each task has an **ID**, **Importance** (1 = nice-to-have, 5 = critical), and an **Order** value (suggested execution sequence, lower runs first).

See `CONVERSIONS.md` for the full input/output spec.
See `DONE.md` for completed work.
See `recommendations.md` for review notes (R-001 through R-007).

## Active

| ID | Order | Importance | Title | Notes |
|----|-------|------------|-------|-------|
| T-001 | 1 | 4 | Deploy fixed `prod/date-formatter-gui.py` and `prod/user-manual.html` to `%USERPROFILE%\scripts\` on client machine | Validates all fixes (Issue 1, Issue 2, GUI polish, logging, JSON settings sidecar, user manual button) in real Windows env. Smoke-test with `9200-W22.xlsx`. Dependency upgrade required on client machine: `pip install --upgrade openpyxl==3.1.5` (or `py -m pip install --upgrade openpyxl==3.1.5` if `pip` is not on PATH). Verify with `py -c "import openpyxl; print(openpyxl.__version__)"`. After first launch the script creates `dates-formatter-settings.json` next to itself, which is expected. |
| T-010 | 2 | 2 | Bundle as Windows installer (PyInstaller or similar). Pinned for later. | So end users do not need to install Python separately. T-005 unblocked this. The sidecar path uses `os.path.dirname(os.path.abspath(__file__))` which points into a PyInstaller temp extract dir when frozen. Will need a path switch to `%APPDATA%\date-formatter\dates-formatter-settings.json` at bundle time. The same applies to `MANUAL_PATH`. |
