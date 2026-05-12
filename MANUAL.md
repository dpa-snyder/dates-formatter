# Date Formatter: User Manual

A guide to using the Date Formatter app to standardize date columns in Excel and CSV spreadsheets.

## What this app does

Archival spreadsheets often contain dates entered in many different ways: `5/8/2026`, `May 8, 2026`, `2026-05-08`, `circa 2026`, `1960s`, `n.d.`, and so on. The Date Formatter reads each value in a column you choose and rewrites it in a single consistent format. Values it cannot confidently parse are left alone and flagged for review.

You select the file, you select the columns, and the app shows you which rows it was uncertain about.

## Launching the app

### If your IT Admin set this up

You have a desktop shortcut, typically called `date-formatter-gui.bat`. Double-click it to launch the app.

If the shortcut is not on your desktop, ask your IT Admin where they placed it.

### Manual launch

Open Command Prompt and run:

```
py %USERPROFILE%\scripts\date-formatter-gui.py
```

Your IT Admin may have configured a different path.

## The window at a glance

The app window contains five sections from top to bottom.

1. **Conversion Type.** Three radio buttons. Select the output style you need.
2. **File.** A Browse button to select an Excel or CSV file.
3. **Columns to Format.** Checkboxes for every column in the loaded file. Tick the columns containing dates.
4. **Run.** Starts the conversion.
5. **Progress bar and status text.** Shows progress and the number of flagged rows.

A sun and moon switch in the top right corner toggles light and dark mode. Your preference is saved between launches.

## Step 1: Pick a conversion mode

The three modes produce different output styles. Pick the one that matches the system you are feeding the cleaned data into.

### Single Date Conversion: `MM/DD/YYYY`

Use this when each row should resolve to a single date.

* `5/8/2026` becomes `05/08/2026`.
* `May 8, 2026` becomes `05/08/2026`.
* If the original value is a range like `01/01/1962 - 12/31/1962`, the output is the start date `01/01/1962`.
* Vague values such as `circa 1962`, `1960s`, `before 1991`, or `undated` produce an empty result and are flagged for review.

### ArchivERA / Date Range Conversion: `MM/DD/YYYY - MM/DD/YYYY`

Use this when each row represents a span of time. This mode is designed for ArchivERA imports.

* `1962` becomes `01/01/1962 - 12/31/1962`.
* `Jun 1962` becomes `06/01/1962 - 06/30/1962`.
* `1960s` becomes `01/01/1960 - 12/31/1969`.
* `5/8/2026` stays as `05/08/2026`.
* Fuzzy values are preserved and flagged: `circa 1962`, `before 10/15/1991`, `after 1991`, `undated`.

### Dublin Core Conversion

Use this when you need Dublin Core-friendly date output. Like ArchivERA, this mode emits dates as ranges. It accepts a wider variety of inputs than ArchivERA, including ISO and Dublin Core partial formats (`2026-05-08`, `1962-1965`, `1962-06/1965-08`, `YYYY-MM-DD/YYYY-MM-DD`).

If you are unsure which mode to pick, use **Date Range**. Dublin Core handles the same range outputs plus more exotic input formats.

## Step 2: Open your file

Click **Browse** and select the Excel (`.xlsx`) or CSV file. Once loaded:

* The filename appears in the file box.
* The Columns section fills with one checkbox per column.
* The status bar shows the row count.

The app reads every column as text. Leading zeros, codes like `001.001`, and folder numbers like `04` are preserved exactly as they appear in the source.

## Step 3: Pick your date columns

Tick every column you want converted. You can pick more than one in a single run, for example both `Full Date` and `Date Checked`. Each column is processed independently in the order ticked.

Columns you do not tick are left exactly as they were.

## Step 4: Run it

Click **Run**. The progress bar advances as the app works through each column. The status line shows the current row and column.

**Important:** when the run finishes, your original file is overwritten with the cleaned version. Make a backup copy before running if you want to keep the raw input.

If the file is open in Excel when the app tries to save, you will see a "File in use" prompt. Close Excel and click Retry.

## Understanding the output

For every column you ticked, the app adds two new columns next to it.

| Column | Contents |
|--------|----------|
| `{your column}` | The cleaned, formatted date. Replaces the original value in place. |
| `Original_{your column}` | The raw original value. |
| `Check {your column}` | `Yes` if the app was uncertain about the row. Blank otherwise. |

For example, if you ticked **Full Date**, the result looks like:

```
... | Full Date | Original_Full Date | Check Full Date | ...
```

When the run finishes, the status bar reports the number of flagged rows. A row is flagged when:

* The original value was vague (`circa 1962`, `before 1991`).
* The app could not recognize the format.
* The original cell contained multiple values separated by semicolons.
* The result did not match a strict `MM/DD/YYYY` or `MM/DD/YYYY - MM/DD/YYYY` shape.

Flagged rows are not errors. They are rows that benefit from a human glance.

## Built-in safeguards

Every formatted output respects three rules:

* **Correct day counts per month.** February has 28 days (29 in leap years). April, June, September, and November have 30. The rest have 31. The app never emits an invalid date like `02/30/1990` or `04/31/1990`.
* **Leap-year awareness.** February 29 only appears in years where it is valid. A year is a leap year if it is divisible by 4, except century years which must also be divisible by 400. So `02/29/2000` is valid and `02/29/1900` is not.
* **Chronological order.** In any output range `start - end`, the start date is on or before the end date. If the input had them reversed, the app swaps them before saving.

If the input itself is an invalid date (for example `02/30/1990`), the app leaves it alone and flags the row for review rather than guessing what was meant.

## Special outputs

These values appear when the input expresses something more nuanced than a plain date or range. They are always flagged.

| Output | Meaning |
|--------|---------|
| `undated` | The original said `n.d.`, `no date`, `not dated`, etc. |
| `circa 1962` | The original said `circa 1962`, `ca. 1962`, `approx. 1962`, etc. |
| `before 01/01/1991` | The original said `before 1991`, `pre-1991`, or `ante 1991`. |
| `before 10/15/1991` | The original gave a specific cutoff date with "before". |
| `after 12/31/1991` | The original said `after 1991` or `post-1991`. |
| `after 10/15/1991` | The original gave a specific cutoff date with "after". |

For year-only inputs, "before" lands on January 1 of that year and "after" lands on December 31. This is a tight bound: the named year is excluded from the range.

## What gets cleaned vs. what stays the same

### Always cleaned, regardless of mode

The following archival ID columns have their leading zeros restored on every save.

| Column header (any variant) | Format |
|-----------------------------|--------|
| `RG`, `Record Group Number` | Exactly 4 digits. `200` becomes `0200`. `9200` stays `9200`. |
| `SG`, `SubGr`, `SubGroup`, `Subgroup Number` | Exactly 3 characters. `22` becomes `022`. `W22` stays `W22`. Single-letter prefix is preserved. |
| `Series`, `Series Number` | Same as SG. |
| `SubSeries Number` | Same as SG. |

### Left alone

Every other column in your spreadsheet, including Folder Number, Sequential Box Number, Title, Description, and Container Barcode, is preserved exactly as it appeared in the source. Leading zeros are kept and codes like `001.001` are not converted to numbers.

## Patterns the app recognizes

The conversion engine tries many input formats. Below are the most common patterns grouped by type. For the full parser-order reference, see `CONVERSIONS.md`.

### Already-formatted dates

| Input | Output |
|-------|--------|
| `05/31/1964` | `05/31/1964` |
| `01/01/1962 - 12/31/1962` | `01/01/1962 - 12/31/1962` |
| `5/8/2026` | `05/08/2026` |

### Years and decades

| Input | Output |
|-------|--------|
| `1962` | `01/01/1962 - 12/31/1962` |
| `1962-1965` | `01/01/1962 - 12/31/1965` |
| `1962-65` | `01/01/1962 - 12/31/1965` |
| `1960s` | `01/01/1960 - 12/31/1969` |

### Month and year

| Input | Output |
|-------|--------|
| `June 1962` | `06/01/1962 - 06/30/1962` |
| `Jun 1962` | `06/01/1962 - 06/30/1962` |
| `Jun-62` | `06/01/1962 - 06/30/1962` |
| `June 5, 1964` | `06/05/1964` |
| `June 5th, 1964` | `06/05/1964` |

### Month and year ranges

| Input | Output |
|-------|--------|
| `June 1, 1962 - August 5, 1964` | `06/01/1962 - 08/05/1964` |
| `June 1 - 5 1962` | `06/01/1962 - 06/05/1962` |
| `1962/06 - 1962/08` | `06/01/1962 - 08/31/1962` |

### ISO and Dublin Core formats

Best handled in Dublin Core mode.

| Input | Output |
|-------|--------|
| `2026-05-08` | `05/08/2026` |
| `2026-05-08 14:30:00` | `05/08/2026` |
| `1962-06/1965-08` | `06/01/1962 - 08/31/1965` |
| `1962-06-05/1965-08-12` | `06/05/1962 - 08/12/1965` |

### Fuzzy and approximate dates

Always flagged.

| Input | Output |
|-------|--------|
| `circa 1962` | `circa 1962` |
| `ca. 1962` | `circa 1962` |
| `approx 1962` | `circa 1962` |
| `before 1991` | `before 01/01/1991` |
| `pre-1991` | `before 01/01/1991` |
| `ante 1991` | `before 01/01/1991` |
| `before 10/15/1991` | `before 10/15/1991` |
| `after 1991` | `after 12/31/1991` |
| `post-1991` | `after 12/31/1991` |
| `n.d.`, `N.D.`, `no date`, `undated` | `undated` |

### Wildcards and incomplete inputs

| Input | Output |
|-------|--------|
| `06/??/1962` | `06/01/1962 - 06/30/1962` |
| `06/00/1962` | `06/01/1962 - 06/30/1962` |
| `?? - 10/15/1991` | `before 10/15/1991` |
| `10/15/1991 - ??` | `after 10/15/1991` |

### Excel serial numbers

Sometimes pasted from older workbooks.

| Input | Output |
|-------|--------|
| `44197` | `01/01/2021` |

### Unrecognized inputs

If the app does not have a pattern for the input, the value is left as-is and the `Check` column is set to `Yes`.

| Input | Output | Check |
|-------|--------|-------|
| `Spring 1962` | `Spring 1962` | `Yes` |
| `Easter 1964` | `Easter 1964` | `Yes` |
| Any free-text comment | passed through | `Yes` |

The app flags rather than guesses.

## If something goes wrong

### Error dialog

Click OK. The app writes a log file to `%TEMP%\date-formatter.log`. Open it in Notepad to see details. Share the log with your IT Admin if you need help.

### "File in use" prompt

Close the spreadsheet in Excel or whatever has it open, then click Retry.

### The app does not open

Python may not be installed, or the script path may have changed. Contact your IT Admin.

### A row was flagged that should not have been

Check the `Original_` column for the raw value the app saw. If the format is one the app does not recognize, you can either clean up the source value and re-run, or edit the formatted column directly.

## Tips

* Make a backup copy of your spreadsheet before running. The app overwrites your file in place.
* Run on one column at a time until you are comfortable with the output, then batch larger jobs.
* After a run, sort by the `Check` column to bring flagged rows to the top.
* The app handles `.xlsx` and `.csv`. Save older `.xls` files as `.xlsx` first.
* Light mode and dark mode are both supported. Your preference is saved.

## Need help

Contact your IT Admin or whoever provided this app. Include the log file from `%TEMP%\date-formatter.log` if you encountered a specific error.

## About this app

Diagnostic info you may be asked to share with your IT Admin.

| Item | Where to find it |
|------|------------------|
| App version | Shown at the bottom-left of the app window. |
| Log file | `%TEMP%\date-formatter.log` on Windows. Records run history and any errors. |
| Settings file | `dates-formatter-settings.json` in the same folder as the script. Stores theme, window position, recent files, and output preference. |
| User manual file | `user-manual.html` in the same folder as the script. |
| Python dependencies | `customtkinter 5.2.2`, `pandas 2.2.2`, `openpyxl 3.1.5`. |

To reset the app to defaults, close the app, delete `dates-formatter-settings.json`, and relaunch.
