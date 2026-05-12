# Dates Formatter

A GUI-based Python app for normalizing inconsistent date formats in Excel and CSV spreadsheets. Designed for archival and records management workflows where date fields contain a wide variety of input formats that need to be standardized before import or export.

## App modes

The app provides three conversion options in a single interface.

| Mode | Output | Use case |
|------|--------|----------|
| Single Date Conversion | `MM/DD/YYYY` | Records that should resolve to a single normalized date |
| ArchivERA Conversion | `MM/DD/YYYY - MM/DD/YYYY` | Records that should resolve to a normalized date range |
| Dublin Core Conversion | Dublin Core-friendly date output (ranges and single dates) | Convert mixed inputs into Dublin Core format |

## Output guarantees

Every formatted output respects three invariants regardless of mode.

* Days per month follow the calendar. The app never emits `02/30/1990` or `04/31/1990`.
* February 29 only appears in valid leap years (divisible by 4, except century years not divisible by 400).
* In any output range `start - end`, the start date is on or before the end date. Reversed inputs are swapped before saving.

Invalid input dates are not corrected. They are passed through unchanged and flagged for review.

## Column output

After running any mode, three columns appear together in the spreadsheet.

| Column | Description |
|--------|-------------|
| `{chosen column}` | Formatted date output. Replaces the original value in place. |
| `Original_{chosen column}` | Original raw value preserved for review |
| `Check {chosen column}` | `Yes` if the output needs manual review |

## Documentation

| Document | Purpose |
|----------|---------|
| `MANUAL.md` and `user-manual.html` | End-user guide. The HTML version is opened from the app's "View User Manual" button. |
| `CONVERSIONS.md` | Technical reference. Per-mode input/output tables in parser order. |
| `TODOS.md` | Active task list. |
| `DONE.md` | Completed work archive. |
| `recommendations.md` | Review notes and findings (IDs `R-001`+). |

## Structure

```text
prod/                          # Stable, deployment-ready scripts
  date-formatter-gui.py
  date-formatter-gui.bat
  user-manual.html             # Opened by the in-app "View User Manual" button
  date-formatter-single.py     # Legacy single-mode script
  date-formatter-range.py      # Legacy range-mode script
  dublin-core-date-convert.py  # Legacy Dublin Core script

src/                           # Active development
  date-formatter-gui.py
  user-manual.html

test-files/                    # Sample spreadsheets
tests/                         # unittest suite

ASSOCIATIONS.md                # Launcher and deployment reference
requirements.txt
```

## Requirements

```text
customtkinter==5.2.2
pandas==2.2.2
openpyxl==3.1.5
```

Install with:

```bash
pip install -r requirements.txt
```

## Deploying to Windows

Copy `date-formatter-gui.py` and `user-manual.html` from `prod/` to:

```text
%USERPROFILE%\scripts\
```

Both files must live in the same folder so the "View User Manual" button can find the HTML.

The batch launcher can live anywhere convenient, including the Desktop. It points back to:

```text
%USERPROFILE%\scripts\date-formatter-gui.py
```

To install the desktop launcher, copy `date-formatter-gui.bat` from `prod/` to the Desktop and launch it.

## Automated tests

The repo includes a small `unittest` suite that reads cases directly from the Excel fixtures in `test-files/`.

Run everything with:

```bash
./run-tests.sh
```

Or run the underlying command directly:

```bash
python3 -m unittest discover -s tests -q
```

The suite is split into smoke tests for fixture rows that should already work, and expected-failure regression tests for known TODO bugs. When a TODO is fixed, remove that test's `expectedFailure` marker and keep the fixture row as a permanent regression check.
