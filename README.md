# Leading Zeros Dates

A set of Python scripts for normalizing inconsistent date formats in Excel/CSV spreadsheets. Designed for archival and records management workflows where date fields contain a wide variety of input formats that need to be standardized for data entry or export.

---

## Scripts

There are three variants, each targeting a different output format. All three share the same structural behavior.

| Script | Output Format | Use Case |
|--------|--------------|----------|
| `date-formatter-single.py` | `MM/DD/YYYY` | Records with a single date value |
| `date-formatter-range.py` | `MM/DD/YYYY - MM/DD/YYYY` | Records with date ranges |
| `dublin-core-date-convert.py` | `MM/DD/YYYY` or `MM/DD/YYYY - MM/DD/YYYY` | Dublin Core metadata format |

See [ASSOCIATIONS.md](ASSOCIATIONS.md) for which `.bat` launcher maps to which script.

---

## Column Output

After running any script, three columns appear together in the spreadsheet:

| Column | Description |
|--------|-------------|
| `{chosen column}` | Formatted date output (replaces original in-place) |
| `Original_{chosen column}` | Original raw value preserved for review |
| `Check {chosen column}` | `Yes` if the output needs manual review |

---

## Structure

```
prod/                        # Stable, deployment-ready scripts
  date-formatter-single.py
  date-formatter-range.py
  dublin-core-date-convert.py
  AE-ranged-date-converter.bat
  dublin-core-date-converter.bat
  govserv-date-converter.bat

src/                         # Active development
  date-formatter-single.py   # Current dev version

test-files/                  # Sample/test spreadsheets

ASSOCIATIONS.md              # Bat → script mapping reference
requirements.txt
```

---

## Requirements

```
customtkinter==5.2.2
pandas==2.2.2
openpyxl==3.1.2
```

Install with:
```
pip install -r requirements.txt
```

---

## Deploying to Windows

Copy the relevant script(s) from `prod/` to `%USERPROFILE%\scripts\` on the target machine, then run the corresponding `.bat` file.

---

## Automated Tests

The repo now includes a small `unittest` suite that reads cases directly from the Excel fixtures in `test-files/`.

Run everything with:
```
./run-tests.sh
```

Or run the underlying command directly:
```
python3 -W ignore::DeprecationWarning -m unittest discover -s tests -q
```

The suite is split into:
- smoke tests for fixture rows that should already work
- expected-failure regression tests for known TODO bugs

When we fix a TODO item, we can remove that test's `expectedFailure` marker and keep the fixture row as a permanent regression check.
