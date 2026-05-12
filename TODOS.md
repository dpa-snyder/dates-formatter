# TODOs

Indexed task list. Each task has an **ID**, **Importance** (1 = nice-to-have, 5 = critical), and an **Order** value (suggested execution sequence, lower runs first).

See `CONVERSIONS.md` for the full input/output spec.
See `DONE.md` for completed work.
See `recommendations.md` for review notes (R-001 through R-007).

## Active

| ID | Order | Importance | Title | Notes |
|----|-------|------------|-------|-------|
| T-001 | 1 | 4 | Deploy fixed `prod/date-formatter-gui.py` and `prod/user-manual.html` to `%USERPROFILE%\scripts\` on client machine | Validates all fixes plus the GUI refresh (cards, stepper, segmented theme, search, recent files, mode hint, output mode, completion dialog, status panel) in real Windows env. Smoke-test with `9200-W22.xlsx`. Dependency upgrade required: `pip install --upgrade openpyxl==3.1.5` (or `py -m pip install --upgrade openpyxl==3.1.5` if `pip` is not on PATH). Verify with `py -c "import openpyxl; print(openpyxl.__version__)"`. After first launch the script creates `dates-formatter-settings.json` next to itself, which is expected. |
| T-010 | 2 | 2 | Bundle as Windows installer (PyInstaller or similar). Pinned for later. | So end users do not need to install Python separately. T-005 unblocked this. The sidecar path uses `os.path.dirname(os.path.abspath(__file__))` which points into a PyInstaller temp extract dir when frozen. Will need a path switch to `%APPDATA%\date-formatter\dates-formatter-settings.json` at bundle time. The same applies to `MANUAL_PATH`. |
| T-013 | 3 | 3 | G-04: Auto-detect date-looking columns on file load | When the file loads, scan each column. For columns where most non-empty values match a date pattern, pre-check the box and/or surface them at the top with a small "looks like dates" badge. Today the mode hint already does the reverse check (column vs current mode). This task is about positive detection. |
| T-014 | 4 | 2 | G-06: Keyboard shortcuts | Bind `Ctrl+O` (browse), `Ctrl+R` (run), `Ctrl+,` (settings, blocked on T-017), `Ctrl+/` (open manual). Mac equivalents (`Cmd+`). |
| T-015 | 5 | 2 | G-12: Drag-and-drop file zone | Requires the `tkinterdnd2` dependency (add to `requirements.txt`). Wrap the file card area as a drop target. Highlight on `<<DropEnter>>`, call `_load_file()` on `<<Drop>>`. Falls back gracefully if the library is missing. |
| T-016 | 6 | 2 | G-17: Settings dialog | Modal opened by `Ctrl+,` or a gear icon. Centralize: default mode, default output behavior, output folder, theme, log level. May need a new `CTkToplevel` subclass. No new deps required. |
