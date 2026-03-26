# Action Plan

---

## Phase 1 — Script Standardization ✓ Complete

### Goals
Bring all three date formatter variants to a consistent structure, add prod versions for all, and clean up the repo.

### Completed

**Script structure (all 3 prod scripts now share this behavior):**
- Chosen column is replaced in-place with formatted output
- `Original_{column}` inserted immediately after — preserves raw value for review
- `Check {column}` inserted after that — flags `Yes` if output needs manual review
- Check column is consistent: all three output `Yes` (previously range/dublin core used `Y`)

**Prod versions established:**
- `prod/date-formatter-single.py` — created (was only in `src/`)
- `prod/date-formatter-range.py` — updated with new column structure
- `prod/dublin-core-date-convert.py` — updated with new column structure

**Documentation:**
- `ASSOCIATIONS.md` — maps each `.bat` launcher to its script, deployed path, and output format
- `README.md` — project overview, structure, deployment instructions
- `TODOS.md` — pinned and pending items
- `ACTION-PLAN.md` — this file

**Cleanup:**
- Removed stale `src/` files: `leading-zeros-dates.py`, `format-cleanup.py`
- Removed stale `test-scripts/`: `dublin-core-date-convert.py`, `serial-excel-dates.py`, `test-named-range.py`
- Moved `.venc/` from `prod/` to repo root; added to `.gitignore`
- Deleted untracked sensitive test file from `test-files/`

---

## Phase 2 — GUI

### Goals
Replace the current tkinter file picker / column dropdown with a proper GUI that gives users more control and visibility.

### Status
Not started. Details TBD.

---

## Backlog

- Resolve govserv bat/script name mismatch (see TODOS.md)
- Rebuild `.venc/` at root after move
- Decide fate of empty `test-scripts/` directory
