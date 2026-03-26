# TODOs

Ongoing and pinned items. See ACTION-PLAN.md for completed work.

---

## P0 — Bug Fixes (identified from test output analysis)

These are confirmed bugs with wrong or garbled output. Highest priority.

---

### ALL SCRIPTS — Year-only values misread as Excel serial numbers
Values like `1900` or `1980` are 4-digit years but fall within the Excel serial number range. The scripts interpret them as serials and produce completely wrong dates (e.g. `1980` → `06/02/1905`).
- **Affects:** Single (rows 91, 94 — unflagged), Range
- **Fix:** Check if a 4-digit value is a plausible year (1000–2100) before treating it as a serial number.

---

### SINGLE — Month-name + year parsed incorrectly
`February 2001` → `02/20/2001` (the "20" from "2001" is grabbed as the day).
`October 1783` → `10/17/1983` (century dropped, day fabricated).
- **Affects:** Single (rows 120, 121, 122 — unflagged)
- **Fix:** When the input is Month + 4-digit year with no day, do not attempt to parse a day from the year digits. Flag or output a range instead.

---

### SINGLE — Excel serial off by one
Serial `40178` resolves to `12/31/2009` instead of `01/01/2010`.
- **Affects:** Single (row 43 — unflagged)
- **Fix:** Audit the serial-to-date conversion formula for edge cases at year boundaries.

---

### RANGE — Excel serial treated as literal year
Serial `40178` produces `01/01/40178 - 12/31/40178` instead of `01/01/2010`.
- **Affects:** Range (row 43 — flagged but output is broken)
- **Fix:** Same serial detection logic as above — convert before treating as a year.

---

### RANGE — Parenthetical content corrupts output
`2016 (Jan., Feb., March, Apr., May, June, Dec.)` → parenthetical text is copied verbatim into both the start and end date slots, producing a completely invalid string.
- **Affects:** Range (row 40 — flagged but output is broken)
- **Fix:** Strip parenthetical content before processing; preserve it in the Original_ column.

---

### RANGE — Zero-day notation not expanded to full month range
`05/0/1776` → `05/00/1776` instead of `05/01/1776 - 05/31/1776`.
- **Affects:** Range (rows 100–102 — flagged but output is wrong format)
- **Fix:** Detect `/0/` day notation and expand to first–last of that month.

---

### DUBLIN CORE — Abbreviated year range produces month=75
`1974-75` → `75/01/1974 - 75/31/1974`. The "75" is interpreted as a month number.
- **Affects:** Dublin Core (row 23 — unflagged). Most severe bug across all three files.
- **Fix:** Detect abbreviated year ranges (`YYYY-YY`) and expand correctly to `01/01/YYYY - 12/31/YYYY+n` before any other parsing.

---

### DUBLIN CORE — Out-of-order date ranges not reordered
`01/01/1857 - 01/01/1855` is passed through uncorrected. The range script handles this correctly (`ensure_chronological_order`); dublin-core does not.
- **Affects:** Dublin Core (rows 11, 75, 76 — unflagged)
- **Fix:** Apply `ensure_chronological_order` in the dublin-core pipeline.

---

### DUBLIN CORE — Missing conversions present in range script
The following input types are converted correctly by the range script but echoed verbatim (and flagged) by dublin-core:
- ISO datetime strings (`1999-01-01 00:00:00`)
- Undated markers (`nd`, `n.d.`, `N.D.`, `ud`, `UD`) — should output `undated`
- Circa variants (`c. 1798`, `c 1999`)
- Before/after/post/pre/ante variants
- Month-name + year without day

- **Affects:** Dublin Core — 116 of 137 rows (85%) flagged, many unnecessarily
- **Fix:** Port the relevant conversion logic from `custom_format_date` into `convert_date_pattern`, or call shared helpers.

---

## Pinned

### govserv bat/script name mismatch
`govserv-date-converter.bat` deploys as `gov-serv-date-formatter.py` but the prod script is named `date-formatter-range.py`. Needs to be reconciled — either rename the prod script or update the bat.
> Tracked in ASSOCIATIONS.md as well.

---

## Next Phase

### GUI
Build a graphical interface for the scripts so users don't need to interact with the column-selection dropdown via tkinter. Details TBD.

---

## Housekeeping

### Venv at root
`.venc/` was moved from `prod/` to repo root. Activation scripts inside have stale paths. Rebuild with:
```
python -m venv .venc
pip install -r requirements.txt
```

### test-scripts/ is now empty
Directory exists but has no contents after cleanup. Can be removed or repopulated with actual tests.

### Suppress openpyxl deprecation warning during tests
`openpyxl` emits a Python 3.13 deprecation warning (`datetime.utcnow()`) during fixture reads. Current workaround is to suppress it in the test command.
