# Done

Completed work archive. Each item references the resolution.

| ID | Title | Resolution |
|----|-------|------------|
| D-001 | Issue 1 — leading zeros stripped on non-chosen columns (`001.001` → `1.001`, `008` → `8`) | Fixed in `_browse` (read with `dtype=str, keep_default_na=False`) and `_save_with_retry` (Excel cells written with `number_format = '@'`). Verified on `9200-W22.xlsx`. |
| D-002 | Issue 2 — alphanumeric SG (`W22`) crashes with `ValueError` | Replaced `int(x)`-based padder with `_pad_alnum(val, width)` helper. Pure numerics zero-pad; single-letter prefixes preserved with digits padded to fit width. No crash on unknown shapes. |
| D-003 | `before`/`pre`/`ante` + `after`/`post` not unified, didn't accept full-date input | Replaced three single-line regexes in both `custom_format_date` and `convert_date_pattern` with one unified regex that captures keyword + (year OR full date), normalizes month/day padding, expands year to tight bound. |
| D-004 | Test suite import path broken (`src/gui.py` no longer exists) | Updated `tests/test_excel_fixtures.py` GUI_PATH to `src/date-formatter-gui.py`. Suite passes 13/13. |
| D-005 | Conversion behavior undocumented for users | Created `CONVERSIONS.md` with full per-mode input/output table in parser order. |
| D-006 | T-002 — confirm `before`/`after` year-bound interpretation | **Tight bound confirmed** by client. `before YYYY` → `before 01/01/YYYY`, `after YYYY` → `after 12/31/YYYY`. No code change needed. |
| D-007 | T-003 — decide handling of unrecognized SG shapes | Client confirmed: SG is only `###` or `C##` format. Current `_pad_alnum` behavior already matches — pads to canonical shape when possible, passes through unrecognized shapes (e.g. `12A`, `W2X`) unchanged. No code change. |
| D-008 | T-007 — log uncaught exceptions to file | Added `logging` module config writing to `%TEMP%/date-formatter.log` (or `/tmp/`). `_run_all` now logs run start, completion, and full traceback on unhandled exception. Error dialog points user to log path. |
| D-009 | T-009 — polish GUI for end users | Added per-mode help text under each radio button, clearer status text when rows are flagged ("X flagged for review (see 'Check ...' column)" vs "no rows flagged"). |
| D-010 | T-011 — suppress openpyxl deprecation in tests | Bumped `requirements.txt` to `openpyxl==3.1.5` (fixes `datetime.utcnow()` deprecation under Python 3.13). Removed `-W ignore::DeprecationWarning` from `run-tests.sh`. **Client must update dependencies on their Windows machine** — re-run `pip install -r requirements.txt` to pick up new version. |
| D-011 | T-012 — output column naming convention | Default to existing code/README convention: `Original_{column}` + `Check {column}`. No rename. |
| D-012 | T-004 — template placeholder rows (e.g. literal `MM/DD/YYYY` in date column) | Closed as **no change needed** — current pipeline already flags such rows with `Check = Yes`, which matches client preference ("ignore but flag in check column"). |
| D-013 | T-005 / R-001 — theme persistence rewriting running script | Replaced `_persist_theme_mode` with JSON sidecar at `dates-formatter-settings.json` next to the deployed script. Added `load_settings` / `save_settings` helpers, default theme `dark`. Added `dates-formatter-settings.json` to `.gitignore` so per-user state isn't committed. |
| D-014 | T-006 — `convert_strange_named_ranges` single-side-year inputs | Client confirmed: current behavior is correct. Inputs like `June 1 1940 - July 2` pass through unchanged with `Check = Yes` so a human can resolve them. No code change. |
| D-015 | T-008 / R-003 — SG header variants treated as one field | Client confirmed: current behavior is correct. `apply_leading_zeros` continues to treat `SG`, `SubGr`, `SubGroup`, `Subgroup Number` as the same field. No code change. |
