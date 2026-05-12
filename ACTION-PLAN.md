# Action Plan

## Phase 1: Script Standardization (Complete)

### Goals

Bring all three date formatter variants to a consistent structure, add prod versions for all, and clean up the repo.

### Completed

Script structure (all three prod scripts now share this behavior):

* Chosen column is replaced in place with formatted output.
* `Original_{column}` inserted immediately after, preserving raw value for review.
* `Check {column}` inserted after that. Flags `Yes` if output needs manual review.
* Check column is consistent: all three output `Yes` (previously range and Dublin Core used `Y`).

Prod versions established:

* `prod/date-formatter-single.py` created (was only in `src/`).
* `prod/date-formatter-range.py` updated with new column structure.
* `prod/dublin-core-date-convert.py` updated with new column structure.

Documentation:

* `ASSOCIATIONS.md` maps each `.bat` launcher to its script, deployed path, and output format.
* `README.md` covers project overview, structure, and deployment instructions.
* `TODOS.md` and `DONE.md` track active and completed work.
* `MANUAL.md` and `user-manual.html` are the end-user guides.
* `CONVERSIONS.md` is the technical parser reference.
* `recommendations.md` archives the review report.
* `ACTION-PLAN.md` is this file.

Cleanup:

* Removed stale `src/` files: `date-formatter-single.py` (legacy `leading-zeros-dates.py`), `format-cleanup.py`.
* Removed stale `test-scripts/`: `dublin-core-date-convert.py`, `serial-excel-dates.py`, `test-named-range.py`.
* Replaced the stale root `.venc/` environment with `.venv/`. `.venv/` is the canonical local environment name.
* Deleted untracked sensitive test file from `test-files/`.

## Phase 2: GUI (In progress)

### Goals

Replace the original tkinter file picker and column dropdown with a proper GUI that gives users more control and visibility.

### Status

A single deployed GUI with three in-app conversion modes:

* Single Date Conversion
* ArchivERA Conversion
* Dublin Core Conversion

Polish completed:

* Per-mode help text under radio buttons.
* Clearer status text on completion.
* "View User Manual" button that opens `user-manual.html` in the default browser.
* JSON settings sidecar for theme persistence (`dates-formatter-settings.json`).
* File logging to `%TEMP%\date-formatter.log` for diagnostics.

## Backlog

* Package the GUI deployment flow cleanly for Windows.
* Consider bundling and distribution beyond a Python plus batch launcher (PyInstaller). See `TODOS.md` T-010.
