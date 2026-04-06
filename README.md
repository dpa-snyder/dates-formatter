# Dates Formatter

A GUI-based Python app for normalizing inconsistent date formats in Excel and CSV spreadsheets. It is designed for archival and records management workflows where date fields contain a wide variety of input formats that need to be standardized before import or export.

---

## App Modes

The deployed app provides three conversion options in one interface:

| Mode | Output | Use Case |
| ------ | -------- | ---------- |
| `Single Date Conversion` | `MM/DD/YYYY` | Records that should resolve to a single normalized date |
| `ArchivERA Conversion` | `MM/DD/YYYY - MM/DD/YYYY` | Records that should resolve to a normalized date range |
| `DublinCore Conversion` | Converts common non-DC inputs into DC-friendly output | Mixed-input Dublin Core cleanup |

---

## Column Output

After running any script, three columns appear together in the spreadsheet:

| Column | Description |
| -------- | ----------- |
| `{chosen column}` | Formatted date output (replaces original in-place) |
| `Original_{chosen column}` | Original raw value preserved for review |
| `Check {chosen column}` | `Yes` if the output needs manual review |

---

## Structure

```text
prod/                        # Stable, deployment-ready scripts
  date-formatter-gui.py
  date-formatter-gui.bat
  date-formatter-single.py           # Legacy single-mode script
  date-formatter-range.py            # Legacy range-mode script
  dublin-core-date-convert.py        # Legacy dublin-core script

src/                         # Active development
  date-formatter-gui.py

test-files/                  # Sample/test spreadsheets

ASSOCIATIONS.md              # Launcher/deployment reference
requirements.txt
```

---

## Requirements

```text
customtkinter==5.2.2
pandas==2.2.2
openpyxl==3.1.2
```

Install with:

```bash
pip install -r requirements.txt
```

---

## Deploying to Windows

Copy `date-formatter-gui.py` from `prod/` to:

```text
%USERPROFILE%\scripts\date-formatter-gui.py
```

The batch launcher can live anywhere convenient, including the Desktop. It always points back to:

```text
%USERPROFILE%\scripts\date-formatter-gui.py
```

If you want a Desktop shortcut/workflow, copy this file from `prod/` to the Desktop:

```bat
date-formatter-gui.bat
```

Then launch `date-formatter-gui.bat`. The batch file already points at `%USERPROFILE%\scripts\gui.py`.

---

## Automated Tests

The repo now includes a small `unittest` suite that reads cases directly from the Excel fixtures in `test-files/`.

Run everything with:

```bash
./run-tests.sh
```

Or run the underlying command directly:

```bash
python3 -W ignore::DeprecationWarning -m unittest discover -s tests -q
```

The suite is split into:

- smoke tests for fixture rows that should already work
- expected-failure regression tests for known TODO bugs

When we fix a TODO item, we can remove that test's `expectedFailure` marker and keep the fixture row as a permanent regression check.
