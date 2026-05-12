# Recommendations & Review Report

Review of `src/date-formatter-gui.py` against two client-reported issues, plus the unified `before`/`after` patch and supporting cleanup. `prod/date-formatter-gui.py` is currently byte-identical to `src/` — it is the deploy-staging copy, not a parallel codebase.

---

## Status summary

| Item | Status |
|------|--------|
| Issue 1 — leading zeros stripped on non-chosen columns | **Fixed** (D-001) |
| Issue 2 — alphanumeric SG crash | **Fixed** (D-002) |
| `before`/`pre`/`ante` + `after`/`post` unification with full-date support | **Fixed** (D-003) |
| Test suite import path | **Fixed** (D-004) |
| Conversion reference doc | **Done** (D-005, see `CONVERSIONS.md`) |
| `src/` → `prod/` promotion | **In sync** |

Active follow-ups tracked in `TODOS.md` (T-001 … T-012).

---

## Issue 1 — Non-chosen columns lose their formatting (`001.001` → `1.001`)

### Root cause

Two compounding causes:

**A. Pandas read with type inference enabled.** `_browse` previously called `pd.read_csv(path)` / `pd.read_excel(path)` with no `dtype=` argument. Pandas coerced columns that looked numeric — `001.001` became float `1.001`, `008` became int `8`. The damage happened on read, before the user even picked columns. Matches the client's description: *"it doesn't delete anything — the data is all the same."*

**B. `apply_leading_zeros` ran on every recognized column.** Fine for RG/SG/Series/SubSeries (always padded per spec), but it could not rescue Folder Number or Sequential Box Number — those columns were not in its list and were already corrupted on read.

### Fix applied

`_browse`:
```python
if path.endswith('.csv'):
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
else:
    df = pd.read_excel(path, dtype=str, keep_default_na=False)
```

`_save_with_retry` (Excel branch):
```python
with pd.ExcelWriter(path, engine='openpyxl') as writer:
    df.to_excel(writer, index=False)
    ws = writer.sheets[next(iter(writer.sheets))]
    for row in ws.iter_rows(min_row=2):
        for cell in row:
            cell.number_format = '@'
```

`_process_column` `pd.notna(val)` checks rewritten to `if val` (values are strings now; empty cell is `""`, not `NaN`).

### Verified

`9200-W22.xlsx` round-trip: RG `9200`, SG `W22`, Series `001`–`004`, Sequential Box `001.001`, Folder Number `01`–`27` all preserved.

---

## Issue 2 — Alphanumeric SG (`W22`) crashes with `ValueError`

### Root cause

```python
df[col] = df[col].apply(lambda x: f'{int(x):03d}' if pd.notna(x) and x != '' else x)
```

`int("W22")` → `ValueError`. The crash bubbled up to the catch-all in `_run_all` and surfaced as a generic error dialog.

### Fix applied

New helper `_pad_alnum(val, width)`:

```python
def _pad_alnum(val, width):
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return val
    s = str(val).strip()
    if s == '':
        return s
    m = re.match(r'^([A-Za-z]?)(\d+)$', s)
    if not m:
        return s          # unknown shape — pass through, no crash
    prefix, digits = m.groups()
    pad = max(0, width - len(prefix))
    return f'{prefix}{digits.zfill(pad)}'
```

`apply_leading_zeros` now uses `_pad_alnum(x, 4)` for RG and `_pad_alnum(x, 3)` for the SG/Series/SubSeries family.

### Verified

| Input | Output |
|-------|--------|
| `22` | `022` |
| `W22` | `W22` |
| `W2` | `W02` |
| `W` | `W` |
| `9200` | `9200` |
| `200` | `0200` |
| `""` | `""` |
| `abc` / `12A` | unchanged |

Open question tracked as **T-003** — whether `W2` should pad to `W02` (current) or pass through unchanged.

---

## Unified `before` / `after` parsing (extends pre/ante/post)

### Motivation

Original code only recognized `pre-YYYY`, `post-YYYY`, `ante-YYYY` (year only). English `before` was not recognized, and full-date inputs like `before 10/15/1991` fell through unmatched.

### Patch applied

Single regex in both `custom_format_date` (AE) and `convert_date_pattern` (Dublin Core):

```python
m = re.search(
    r'(?i)\b(?P<kw>before|pre|ante|after|post)\.?\s*-?\s*'
    r'(?P<date>\d{1,2}/\d{1,2}/\d{4}|\d{4})\b',
    date_str)
if m:
    kw = m.group('kw').lower()
    out_kw = 'after' if kw in {'after', 'post'} else 'before'
    raw = m.group('date')
    if '/' in raw:
        mo, d, y = raw.split('/')
        norm = f'{int(mo):02d}/{int(d):02d}/{y}'
    else:
        norm = f'01/01/{raw}' if out_kw == 'before' else f'12/31/{raw}'
    return (f'{out_kw} {norm}', 'Yes')   # convert_date_pattern drops the flag
```

### Behavior

| Input | Output | Flag |
|-------|--------|------|
| `before 10/15/1991` | `before 10/15/1991` | Yes |
| `before 1/5/1991` | `before 01/05/1991` | Yes |
| `before 1991` | `before 01/01/1991` | Yes |
| `pre-1991` / `ante 1991` | `before 01/01/1991` | Yes |
| `after 1991` / `post-1991` | `after 12/31/1991` | Yes |
| `after 10/15/1991` | `after 10/15/1991` | Yes |

Year-only inputs use a **tight bound** (year start for `before`, year end for `after`). Flip pending client confirmation (**T-002**).

Outputs remain flagged `Yes` because open-ended bounds always benefit from human review.

---

## Other findings (smaller, deferred to TODOs)

| Rec ID | Finding | Linked TODO | Status |
|--------|---------|-------------|--------|
| R-001 | **Theme persistence rewrites the running script** (`_persist_theme_mode`). Works in dev, breaks on read-only / frozen installs. Suggested: small JSON sidecar (alongside script for source deploys; `%APPDATA%` for frozen builds). | T-005 | **Resolved** (D-013) — sidecar at `dates-formatter-settings.json` next to the script. |
| R-002 | **Catch-all `except Exception` in `_run_all`** swallowed tracebacks into a generic dialog. Add `logging` to a temp-dir file so field bugs are diagnosable. | T-007 | **Resolved** (D-008) |
| R-003 | **`apply_leading_zeros` treats `SG`, `SubGr`, `SubGroup`, `Subgroup Number` as one field.** Confirm semantics with client — see T-008 for copy-paste question. | T-008 | **Resolved** (D-015) — client confirmed current behavior. |
| R-004 | **Column naming convention drift** — client described expected columns as `Old Full Date` / `Check Me`. Code/README produce `Original_Full Date` / `Check Full Date`. Defaulted to existing code/README convention. | T-012 | **Resolved** (D-011) |
| R-005 | **`src/` vs `prod/` dev/release split is intentional** (per README + ASSOCIATIONS.md). Don't dedupe — `prod/` is the staging buffer for what gets copied to `%USERPROFILE%\scripts\`. Workflow: edit `src/`, smoke-test, then `cp src/... prod/...`. | n/a — workflow note | Acknowledged |
| R-006 | **GUI usability** — add per-mode help text under radio buttons, clearer "X flagged for review" status text on completion. | T-009 | **Resolved** (D-009) |
| R-007 | **openpyxl deprecation warning** during tests was suppressed at the test runner level. Upgrading `openpyxl` to `3.1.5` removes the warning at the source. | T-011 | **Resolved** (D-010) |

---

## Verification

```bash
./run-tests.sh
```

13/13 pass. Real-file regression on `test-files/9200-W22.xlsx`:
- Single Date mode on `Date Checked` — preserves all non-target columns.
- Date Range mode on `Full Date` — preserves all non-target columns; 188 rows, 2 intentional flags (`before 10/15/1991`, `undated`).

Outputs saved under `test-files/test-outputs/`.

---

## Deploy steps

1. `cp src/date-formatter-gui.py prod/date-formatter-gui.py` (already done — `SYNC_OK`).
2. On Windows client machine: copy `prod/date-formatter-gui.py` → `%USERPROFILE%\scripts\date-formatter-gui.py`.
3. Smoke-test using a copy of `9200-W22.xlsx`. Confirm RG/SG/Folder Number/Sequential Box round-trip unchanged.
