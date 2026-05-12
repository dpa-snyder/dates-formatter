# Recommendations and Review Report

Review of `src/date-formatter-gui.py` against two client-reported issues, plus the unified `before` and `after` patch, GUI polish, user manual, and supporting cleanup. `prod/date-formatter-gui.py` and `prod/user-manual.html` are byte-identical to their `src/` counterparts. `prod/` is the deploy-staging copy, not a parallel codebase.

## Status summary

| Item | Status |
|------|--------|
| Issue 1: leading zeros stripped on non-chosen columns | Fixed (D-001) |
| Issue 2: alphanumeric SG crash | Fixed (D-002) |
| `before`, `pre`, `ante`, `after`, `post` unification with full-date support | Fixed (D-003) |
| Test suite import path | Fixed (D-004) |
| Conversion reference doc | Done (D-005, see `CONVERSIONS.md`) |
| Logging | Done (D-008) |
| GUI polish | Done (D-009) |
| openpyxl dependency bump | Done (D-010) |
| JSON settings sidecar | Done (D-013) |
| User manual + in-app button | Done (D-016) |
| Public docs cleanup | Done (D-017) |
| `src/` and `prod/` promotion | In sync |

Active follow-ups tracked in `TODOS.md` (T-001, T-010).

## Issue 1: non-chosen columns lose their formatting (`001.001` becomes `1.001`)

### Root cause

Two compounding causes.

**A. Pandas read with type inference enabled.** `_browse` previously called `pd.read_csv(path)` or `pd.read_excel(path)` with no `dtype=` argument. Pandas coerced columns that looked numeric. `001.001` became float `1.001` and `008` became int `8`. The damage happened on read, before the user even picked columns. Matches the client's description: "it doesn't delete anything, the data is all the same."

**B. `apply_leading_zeros` ran on every recognized column.** Fine for RG, SG, Series, and SubSeries (always padded per spec). It could not rescue Folder Number or Sequential Box Number because those columns are not in its list, and they were already corrupted on read.

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

`_process_column` `pd.notna(val)` checks rewritten to `if val`. Values are strings now. An empty cell is `""`, not `NaN`.

### Verified

`9200-W22.xlsx` round-trip: RG `9200`, SG `W22`, Series `001` through `004`, Sequential Box `001.001`, and Folder Number `01` through `27` are all preserved.

## Issue 2: alphanumeric SG (`W22`) crashes with `ValueError`

### Root cause

```python
df[col] = df[col].apply(lambda x: f'{int(x):03d}' if pd.notna(x) and x != '' else x)
```

`int("W22")` raises `ValueError`. The crash bubbled up to the catch-all in `_run_all` and surfaced as a generic error dialog.

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
        return s          # unknown shape: pass through, no crash
    prefix, digits = m.groups()
    pad = max(0, width - len(prefix))
    return f'{prefix}{digits.zfill(pad)}'
```

`apply_leading_zeros` now uses `_pad_alnum(x, 4)` for RG and `_pad_alnum(x, 3)` for the SG, Series, and SubSeries family.

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
| `abc`, `12A` | unchanged |

## Unified `before` and `after` parsing (extends pre, ante, post)

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
| `pre-1991`, `ante 1991` | `before 01/01/1991` | Yes |
| `after 1991`, `post-1991` | `after 12/31/1991` | Yes |
| `after 10/15/1991` | `after 10/15/1991` | Yes |

Year-only inputs use a tight bound (year start for `before`, year end for `after`). Confirmed with client (D-006).

Outputs remain flagged `Yes`. Open-ended bounds always benefit from human review.

## Findings (with IDs)

| Rec ID | Finding | Linked TODO | Status |
|--------|---------|-------------|--------|
| R-001 | Theme persistence rewrites the running script (`_persist_theme_mode`). Works in dev, breaks on read-only or frozen installs. Suggested: small JSON sidecar (alongside script for source deploys, `%APPDATA%` for frozen builds). | T-005 | Resolved (D-013). Sidecar at `dates-formatter-settings.json` next to the script. |
| R-002 | Catch-all `except Exception` in `_run_all` swallowed tracebacks into a generic dialog. Add `logging` to a temp-dir file so field bugs are diagnosable. | T-007 | Resolved (D-008) |
| R-003 | `apply_leading_zeros` treats `SG`, `SubGr`, `SubGroup`, `Subgroup Number` as one field. Confirm semantics with client. | T-008 | Resolved (D-015). Client confirmed current behavior. |
| R-004 | Column naming convention drift. Client described expected columns as `Old Full Date` and `Check Me`. Code and README produce `Original_Full Date` and `Check Full Date`. Defaulted to existing convention. | T-012 | Resolved (D-011) |
| R-005 | `src/` and `prod/` dev/release split is intentional (per README and ASSOCIATIONS.md). Do not dedupe. `prod/` is the staging buffer for what gets copied to `%USERPROFILE%\scripts\`. Workflow: edit `src/`, smoke-test, then `cp src/... prod/...`. | n/a (workflow note) | Acknowledged |
| R-006 | GUI usability. Add per-mode help text under radio buttons, clearer "X flagged for review" status text on completion. | T-009 | Resolved (D-009) |
| R-007 | openpyxl deprecation warning during tests was suppressed at the test runner level. Upgrading `openpyxl` to `3.1.5` removes the warning at the source. | T-011 | Resolved (D-010) |

## Verification

```bash
./run-tests.sh
```

13 of 13 tests pass. Real-file regression on `test-files/9200-W22.xlsx`:

* Single Date mode on `Date Checked` preserves all non-target columns.
* Date Range mode on `Full Date` preserves all non-target columns. 188 rows, 2 intentional flags (`before 10/15/1991` and `undated`).

Outputs saved under `test-files/test-outputs/`.

## Deploy steps

1. `cp src/date-formatter-gui.py prod/date-formatter-gui.py`
2. `cp src/user-manual.html prod/user-manual.html`
3. On the Windows client machine, copy both files from `prod/` to `%USERPROFILE%\scripts\`. Both must live in the same folder so the "View User Manual" button can find the HTML.
4. Upgrade openpyxl on the client machine: `pip install --upgrade openpyxl==3.1.5`.
5. Smoke-test using a copy of `9200-W22.xlsx`. Confirm RG, SG, Folder Number, and Sequential Box round-trip unchanged.
