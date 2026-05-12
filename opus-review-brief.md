# Opus Review Brief: Date Formatter App

> **Status: superseded.** Review completed on 2026-05-12. All findings produced by this review have been fixed (see `DONE.md` entries D-022 through D-026). The brief is preserved as an audit trail for the review session. For current behavior consult `CONVERSIONS.md`, `MANUAL.md`, and `user-manual.html`. Note: the smoke case `40178 -> 01/01/2010` in this brief reflected the pre-fix Excel serial formula. The current code (and updated fixture) returns `12/31/2009`, matching real Excel display.

This document is a self-contained brief for a full review of the date formatter app. Read it completely before touching any code. Run every test case listed. Report findings in the format specified at the end.

---

## App purpose

A GUI Python app that normalizes inconsistent date strings in Excel and CSV spreadsheets. It processes a user-selected column and writes three output columns: the formatted date in place, `Original_{col}` preserving the raw value, and `Check {col}` flagging rows that need manual review.

---

## File inventory

Only these files matter for this review:

| File | Role |
|------|------|
| `src/date-formatter-gui.py` | Active development copy. Contains all three conversion modes. This is what the test suite imports. |
| `prod/date-formatter-gui.py` | Deployed copy. Must be identical to `src/` version in logic. Diff should show only cosmetic or zero differences. |
| `prod/dublin-core-date-convert.py` | Legacy standalone Dublin Core script. Still deployed via `prod/dublin-core-date-converter.bat`. Must match GUI DC mode behavior. |
| `tests/test_excel_fixtures.py` | Unittest suite. Reads from Excel fixtures in `test-files/`. Run with `./run-tests.sh`. |
| `CONVERSIONS.md` | Authoritative spec for all three modes. Code must match this document. |

The `src/` and `prod/date-formatter-gui.py` files are kept in sync manually. Any logic discrepancy between them is a bug.

---

## Three conversion modes

All three modes output the same date formats:
- Single date: `MM/DD/YYYY`
- Range: `MM/DD/YYYY - MM/DD/YYYY`
- Descriptive tokens: `undated`, `circa YYYY`, `before MM/DD/YYYY`, `after MM/DD/YYYY`

The modes differ only in which input formats they accept. DC is a superset of AE inputs plus DC-specific ISO/partial formats.

### Mode 1: Single Date (`format_single_date`)

Runs the full Date Range pipeline, then collapses any range to its start date. Output is always `MM/DD/YYYY` or empty string. Check = `Yes` if output is not `MM/DD/YYYY`.

### Mode 2: Date Range / ArchivERA (`custom_format_date`)

Returns a tuple `(value, flag)` where `flag` is `'Yes'` or `''`. After conversion, `convert_strange_named_ranges` and `ensure_chronological_order` are applied. A second pass sets Check='Yes' for any output not matching `MM/DD/YYYY`, `MM/DD/YYYY - MM/DD/YYYY`, or `undated`.

Key patterns (first match wins):
- Already-formatted range → pass through
- Strip parens before matching
- Add leading zeros to single-digit month/day
- Already-formatted single `MM/DD/YYYY` → pass through
- 4-digit year 1000-2100 → `01/01/YYYY - 12/31/YYYY`
- Excel serial (5-digit) → single date, Check='Yes'
- Year list `YYYY, YYYY...` → span, Check='Yes'
- Named month range / ordinal day
- No-date markers → `undated`
- Excel serial range
- ISO-ish `YYYY[-/]MM[-/]DD` → single date
- `before/pre/ante/after/post` + year or full date → `before MM/DD/YYYY` / `after MM/DD/YYYY`, Check='Yes'
- ISO timestamp
- Year range `YYYY - YYYY`
- `YYYY/MM - YYYY/MM`
- Decade shorthand `YYYY-YY`
- `?? - date` / `date - ??` → before/after tokens
- Zero-day `M/00/YYYY` patterns
- `circa/ca./approx./c.` → `circa YYYY`, Check='Yes'
- Decade `YYYYs`
- `??` wildcards
- Named month + year
- Fallthrough → unchanged, Check='Yes'

Post-processing: `convert_strange_named_ranges` handles `Jun 1 - Aug 5 1962` style. `ensure_chronological_order` swaps reversed ranges.

### Mode 3: Dublin Core (`convert_date_pattern`)

Returns plain string (no tuple). Check column set after via `dc_valid` pattern list. DC-specific inputs:
- Already `MM/DD/YYYY - MM/DD/YYYY` → pass through
- Strip parens
- Excel serial → single date
- Excel serial range
- No-date markers → `undated`
- ISO timestamp `YYYY-MM-DD HH:MM:SS`
- ISO `YYYY-MM-DD`
- DC range `YYYY-YYYY`
- DC partials: `YYYY/YYYY-MM`, `YYYY-MM/YYYY`, `YYYY-MM/YYYY-MM`
- DC year list `YYYY/YYYY(/YYYY...)`
- ISO range `YYYY-MM-DD/YYYY-MM-DD`
- `YYYY-MM` (month) or `YYYY-YY` (decade shorthand)
- `YYYY` (year)
- Mixed `MM-DD-YYYY/YYYY-MM-DD`
- ISO with `TO` literal → recurse after replacing ` TO ` with `/`
- `before/pre/ante/after/post` + year or full date
- `circa/ca./approx./c.`
- `MonthName YYYY`
- `M/00/YYYY` zero day
- Fallthrough → unchanged

DC does NOT apply `convert_strange_named_ranges`. It DOES apply `ensure_chronological_order` in the pipeline.

---

## Changes made in this session

### Change 1: Legacy DC script — 6 missing handlers added

File: `prod/dublin-core-date-convert.py`

The legacy standalone script `prod/dublin-core-date-convert.py` was missing six handlers that exist in the GUI's `convert_date_pattern`. These were added to match the GUI's DC behavior exactly.

Added helper functions (lines 60-65):
```python
def is_excel_serial_text(value):
    return bool(re.fullmatch(r'\d{5}', str(value)))

def excel_serial_to_date(serial_text):
    return (datetime(1899, 12, 31) + timedelta(days=int(serial_text))).strftime('%m/%d/%Y')
```

Added handlers in `convert_date_pattern`, immediately after strip-parens (before ISO date check):
1. Excel serial (5-digit) → single date
2. Excel serial range `NNNNN - NNNNN` → date range
3. No-date markers (`N.D.`, `n.d.`, `U.D.`, `No Date`, `not dated`) → `undated`
4. ISO timestamp `YYYY-MM-DD HH:MM:SS` → single date

Added handlers after `TO` literal (before `MonthName YYYY`):
5. `before/pre/ante/after/post` + year or full date
6. `circa/cir./ca./approx./c.` + year

### Change 2: `TO` literal recursion fix (all three files)

**Problem:** `1962-06-05 TO 1965-08-12` was handled by replacing `TO` with `-`, producing `1962-06-05 - 1965-08-12`. The recursive call then found no matching pattern and returned the string unchanged.

**Root cause:** The ISO range handler expects `/` as the separator (`YYYY-MM-DD/YYYY-MM-DD`). Replacing `TO` with `-` gave the wrong separator.

**Fix:** Replace ` TO ` (with surrounding whitespace) with `/` using `re.sub`, so the recursive call receives `1962-06-05/1965-08-12` which matches the ISO range handler.

```python
# Before (all three files):
date_str.replace('To', '-').replace('TO', '-').replace('to', '-')

# After:
re.sub(r'\s+(To|TO|to)\s+', '/', date_str)
```

Applied to: `src/date-formatter-gui.py`, `prod/date-formatter-gui.py`, `prod/dublin-core-date-convert.py`.

---

## Invariants that must hold for every output

These apply to all three modes:

1. **Days per month are calendar-correct.** `get_last_day_of_month(year, month)` returns 28/29/30/31 as appropriate. No `02/30`, `04/31`, etc.
2. **Leap year awareness.** February 29 only appears for valid leap years (divisible by 4, except century years not divisible by 400). `02/29/2000` is valid; `02/29/1900` is not.
3. **Chronological order.** Every range satisfies `start <= end`. `ensure_chronological_order` swaps reversed inputs.

---

## How to run the test suite

```bash
cd /path/to/leading-zeros-dates
./run-tests.sh
```

Expected: `Ran 13 tests` with `OK`. No failures, no errors.

The suite imports from `src/date-formatter-gui.py` (not prod). It reads from Excel fixtures in `test-files/`.

---

## Inline test cases to verify manually

Run this Python snippet. It tests `convert_date_pattern` in isolation (copy the function and its helpers, or import from `src/date-formatter-gui.py`).

Expected: 34 passed, 0 failed.

```python
cases = [
    # user-confirmed DC input patterns
    ("1962-06-05",               "06/05/1962"),
    ("1962-06",                  "06/01/1962 - 06/30/1962"),
    ("1962",                     "01/01/1962 - 12/31/1962"),
    ("1962-06-05/1965-08-12",    "06/05/1962 - 08/12/1965"),
    # excel serial — baseline from fixture row 45: serial 40178 = 01/01/2010
    ("40178",                    "01/01/2010"),
    # no-date markers (newly added to legacy)
    ("N.D.",                     "undated"),
    ("n.d.",                     "undated"),
    ("No Date",                  "undated"),
    ("not dated",                "undated"),
    ("U.D.",                     "undated"),
    # ISO timestamp (newly added to legacy)
    ("1962-06-05 14:30:00",      "06/05/1962"),
    # before/after family (newly added to legacy, already in GUI)
    ("before 1991",              "before 01/01/1991"),
    ("before 10/15/1991",        "before 10/15/1991"),
    ("pre-1991",                 "before 01/01/1991"),
    ("ante 1991",                "before 01/01/1991"),
    ("after 1991",               "after 12/31/1991"),
    ("after 10/15/1991",         "after 10/15/1991"),
    ("post-1991",                "after 12/31/1991"),
    # circa family (newly added to legacy, already in GUI)
    ("circa 1962",               "circa 1962"),
    ("ca. 1962",                 "circa 1962"),
    ("approx 1962",              "circa 1962"),
    ("c. 1962",                  "circa 1962"),
    # DC-specific regression cases
    ("01/01/1962 - 12/31/1962",  "01/01/1962 - 12/31/1962"),
    ("1962-1965",                "01/01/1962 - 12/31/1965"),
    ("1962/1965-08",             "01/01/1962 - 08/31/1965"),
    ("1962-06/1965",             "06/01/1962 - 12/31/1965"),
    ("1962-06/1965-08",          "06/01/1962 - 08/31/1965"),
    ("1962/1965/1971",           "01/01/1962 - 12/31/1971"),
    ("1962-65",                  "01/01/1962 - 12/31/1965"),
    ("June 1962",                "06/01/1962 - 06/30/1962"),
    ("06/00/1962",               "06/01/1962 - 06/30/1962"),
    # TO literal fix (all three files)
    ("1962-06-05 TO 1965-08-12", "06/05/1962 - 08/12/1965"),
    ("1962-06-05 to 1965-08-12", "06/05/1962 - 08/12/1965"),
    # paren stripping
    ("1962 (approx)",            "01/01/1962 - 12/31/1962"),
]
```

---

## AE mode spot checks (`custom_format_date`)

These should return `(value, flag)` tuples. Run against `src/date-formatter-gui.py`.

| Input | Expected value | Expected flag |
|-------|----------------|---------------|
| `before 1991` | `before 01/01/1991` | `Yes` |
| `after 10/15/1991` | `after 10/15/1991` | `Yes` |
| `pre-1991` | `before 01/01/1991` | `Yes` |
| `circa 1962` | `circa 1962` | `Yes` |
| `ca. 1962` | `circa 1962` | `Yes` |
| `1962-06-05 TO 1965-08-12` | This input goes through the DC parser, not AE. AE has its own ISO handler at `(\d{4})[-/](\d{1,2})[-/](\d{1,2})` — verify `1962-06-05` → `06/05/1962` with flag `''`. |
| `June 1 - Aug 5 1962` | `06/01/1962 - 08/05/1962` (via `convert_strange_named_ranges`) | `''` |
| `1960s` | `01/01/1960 - 12/31/1969` | `''` |
| `06/??/1962` | `06/01/1962 - 06/30/1962` | `''` |
| `?? - 10/15/1991` | `before 10/15/1991` | `Yes` |
| `10/15/1991 - ??` | `after 10/15/1991` | `Yes` |
| `undated` | `undated` | `''` |
| `N.D.` | `undated` | `''` |

---

## Consistency check: `src/` vs `prod/date-formatter-gui.py`

These two files must have identical logic. Run:

```bash
diff src/date-formatter-gui.py prod/date-formatter-gui.py
```

Expected: empty diff (no output). Any difference is a bug.

---

## Consistency check: Legacy DC script vs GUI DC mode

The legacy `prod/dublin-core-date-convert.py` `convert_date_pattern` function must produce the same output as the GUI's `convert_date_pattern` for every input. Specific checks:

1. All 34 smoke test cases above must pass against the legacy script's function.
2. The legacy function must return `'undated'` for `N.D.`, `n.d.`, `U.D.`, `No Date`, `not dated`.
3. The legacy function must return `'before 01/01/1991'` for `before 1991`.
4. The legacy function must return `'circa 1962'` for `circa 1962`, `ca. 1962`, `approx 1962`, `c. 1962`.
5. The legacy function must return `'06/05/1962 - 08/12/1965'` for `1962-06-05 TO 1965-08-12`.

Note: the legacy script has tkinter initialization at the bottom of the file that prevents direct import. Extract the pure functions (everything before `# Main script execution`) or use `exec` with the relevant portions to test.

---

## Output column check

For all three modes, verify the pipeline writes columns in this order:

1. `{chosen_column}` — formatted output, replaces original in place
2. `Original_{chosen_column}` — raw input preserved
3. `Check {chosen_column}` — `'Yes'` if needs review, `''` otherwise

Check column must be `'Yes'` for: `before`/`after`/`circa` outputs, Excel serial outputs, unrecognized inputs, decade shorthands with ambiguity, inputs containing `;`.
Check column must be `''` for: clean `MM/DD/YYYY`, clean `MM/DD/YYYY - MM/DD/YYYY`, `undated`.

---

## CONVERSIONS.md accuracy check

Verify that the code matches the documented behavior in `CONVERSIONS.md`. Specific items to cross-check:

- DC row 15: `ISO range with TO literal` — now fixed. `1962-06-05 TO 1965-08-12` should produce `06/05/1962 - 08/12/1965`.
- DC rows 16-17: `before/after` and `circa` — confirm these work in both GUI DC and legacy DC script.
- AE row 13: `before/after` handling — confirm tight year bounds: `before 1991` → `before 01/01/1991`, `after 1991` → `after 12/31/1991`.

---

## Edge cases to probe

These are not in the test suite. Check them manually via the inline test or import.

| Input | Mode | Expected |
|-------|------|---------|
| `02/29/2000` | AE/DC | `02/29/2000` (valid leap year) |
| `02/29/1900` | AE/DC | `02/29/1900` (passes through unchanged — invalid date is not corrected, flagged Yes) |
| `12/31/1962 - 01/01/1962` | AE | `01/01/1962 - 12/31/1962` (chronological swap) |
| `1962, 1965, 1971` | AE | `01/01/1962 - 12/31/1971` (year list) |
| `June 1964` | AE/DC | `06/01/1964 - 06/30/1964` |
| `Jun-62` | AE | `06/01/1962 - 06/30/1962` (2-digit year, 62 >= 50 → 1962) |
| `Jun-22` | AE | `06/01/2022 - 06/30/2022` (22 < 50 → 2022) |
| `1962 vol 3` | AE | `01/01/1962 - 12/31/1962`, flag=Yes |
| `Spring 1962` | AE/DC | `Spring 1962` unchanged, flag=Yes |
| `` (empty) | All | `''` or `undated` depending on mode |

---

## What to look for beyond test results

1. **Parser order correctness.** Each pipeline is first-match-wins. A pattern placed too early can shadow a later one. Check that `YYYY-YYYY` (DC row 6) does not shadow `YYYY-YY` (decade shorthand, DC row 12) — they have different regex anchors (`$`) so they should not conflict.

2. **`re.match` vs `re.search` usage.** `re.match` anchors to start. `re.search` scans the whole string. The `before/after` handler uses `re.search` intentionally to find the keyword anywhere in the string. `circa` uses `re.match` — confirm that `circa` inputs are not prefixed with anything unexpected that would break this.

3. **`str(val)` vs raw `val`.** The GUI pipeline calls `convert_date_pattern(val)` and `custom_format_date(val)` with the raw pandas cell value, not `str(val)`. The legacy script uses `str(x)` in its lambda. This is a potential divergence for non-string cell types (e.g., pandas Timestamps). Note any risk but do not change behavior unless clearly broken.

4. **Legacy script `RG`/`SG` column normalization.** The legacy `process_dataframe` uses `int(x)` for RG/SG normalization (line ~211-216), which crashes on alphanumeric values like `W22`. The GUI uses `_pad_alnum`. Flag this if found — it is a pre-existing bug and out of scope for this session's changes, but should be documented.

5. **`prod/` vs `src/` drift.** Any logic difference between `src/date-formatter-gui.py` and `prod/date-formatter-gui.py` is a deployment risk.

---

## Reporting format

Return a single structured report with these sections:

### Test suite result
State pass/fail counts. Quote any failure output verbatim.

### Smoke test result (34 cases)
State pass/fail counts. List every failure with input, expected, and actual.

### AE spot check result
Pass/fail for each row in the AE table above.

### Consistency: src vs prod diff
Quote the diff output or state "no differences".

### Consistency: legacy DC vs GUI DC
State whether the legacy script produces identical outputs to the GUI for all 34 smoke cases.

### Edge case results
Pass/fail for each edge case in the table above. Note any unexpected outputs.

### CONVERSIONS.md accuracy
State whether the documented behavior matches the code for the three items called out. Note any other discrepancies found.

### Findings
Numbered list. Each item: severity (`critical` / `bug` / `warning` / `note`), file and line if applicable, description, and recommended action. Do not repeat passing items here.

### Summary
Two sentences: overall health of the codebase and whether the session's changes are correct and complete.
