# Date Formatter — User Manual

Welcome. This guide walks you through using the Date Formatter app to clean up date columns in your Excel and CSV spreadsheets.

---

## What this app does

Archival spreadsheets often have dates entered in many different ways — `5/8/2026`, `May 8, 2026`, `2026-05-08`, `circa 2026`, `1960s`, `n.d.`, blank cells, and so on. The Date Formatter reads each value in a column you choose, figures out what was meant, and rewrites it in a single consistent format. Anything it can't confidently parse is left alone and **flagged for review**, so a human can take a quick look.

You stay in control: you pick the file, you pick the columns, and the app shows you exactly which rows it wasn't sure about.

---

## Launching the app

### If your IT Admin set this up for you

You'll have a **desktop shortcut** (a `.bat` file, usually called `date-formatter-gui.bat`). Just double-click it. A window will open with the Date Formatter ready to use. No command line, no setup — that's it.

If the shortcut isn't on your desktop, ask your IT Admin where they placed it.

### If you're launching it manually

Open Command Prompt and run:

```
py %USERPROFILE%\scripts\date-formatter-gui.py
```

(Your IT Admin may have configured a different path — check with them if this doesn't work.)

---

## A quick tour of the window

When the app opens, you'll see five sections from top to bottom:

1. **Conversion Type** — three radio buttons. Pick one based on what kind of output you need.
2. **File** — a Browse button to pick the Excel or CSV file you want to clean up.
3. **Columns to Format** — once a file is loaded, every column shows up here as a checkbox. Tick the ones containing dates.
4. **Run** — kicks off the conversion.
5. **Progress bar + status text** — shows what the app is doing and how many rows ended up flagged.

There's also a sun/moon switch in the top right corner to toggle between light and dark mode. Your choice is remembered between launches.

---

## Step 1 — Pick a conversion mode

The three modes produce different output styles. Pick whichever matches the system you're feeding the cleaned data into.

### Single Date Conversion → `MM/DD/YYYY`

Best when each row should resolve to **one** specific date.

- `5/8/2026` becomes `05/08/2026`
- `May 8, 2026` becomes `05/08/2026`
- If the original value was a range (`01/01/1962 - 12/31/1962`), it collapses to the **start** date (`01/01/1962`).
- Vague values (`circa 1962`, `1960s`, `before 1991`, `undated`) become **empty** and get flagged for review.

### ArchivERA / Date Range Conversion → `MM/DD/YYYY - MM/DD/YYYY`

Best when each row represents a span of time. This is the mode designed for ArchivERA-style imports.

- A year like `1962` becomes the full year range `01/01/1962 - 12/31/1962`.
- A month like `Jun 1962` becomes `06/01/1962 - 06/30/1962`.
- A decade like `1960s` becomes `01/01/1960 - 12/31/1969`.
- A single date like `5/8/2026` stays as `05/08/2026`.
- Fuzzy values stay readable: `circa 1962`, `before 10/15/1991`, `after 1991`, `undated` — all preserved and flagged.

### Dublin Core Conversion

Best when you're converting Dublin Core / ISO-style inputs (`2026-05-08`, `1962-1965`, `1962-06/1965-08`) into our standard MM/DD/YYYY format.

If you're not sure which to pick, use **Date Range**. It handles the widest variety of inputs.

---

## Step 2 — Open your file

Click **Browse** and pick the Excel (.xlsx) or CSV file you want to clean up. Once loaded:

- The filename appears in the box.
- The Columns section fills up with one checkbox per column.
- The status bar tells you how many rows were loaded.

The app reads everything as **text**. This is important: it means leading zeros, codes like `001.001`, and Folder Numbers like `04` are preserved exactly as they appear in the source file. Nothing gets converted to a number behind your back.

---

## Step 3 — Pick your date columns

Tick every column you want converted. You can pick more than one — for example, both **Full Date** and **Date Checked** in the same run. Each column gets processed independently in the order you ticked them.

You don't need to worry about non-date columns. Everything you **don't** tick is left exactly as it was.

---

## Step 4 — Run it

Click **Run**. The progress bar will move as the app works through each column. The status line tells you which row and column it's currently on.

When it finishes, your **original file is overwritten** with the cleaned version. So before running, make a backup copy if you want to keep the raw input.

If the file is open in Excel when the app tries to save, you'll get a "File in use" prompt. Close Excel and click Retry.

---

## Understanding the output

For every column you ticked, the app adds **two new columns** right next to it:

| Column | What it contains |
|--------|------------------|
| `{your column}` | The cleaned, formatted date — this **replaces** the original value in place. |
| `Original_{your column}` | The raw original value, kept so you can compare or restore. |
| `Check {your column}` | `Yes` if the app wasn't sure and you should look at this row. Blank otherwise. |

For example, if you ticked **Full Date**, after running you'll see:

`... | Full Date | Original_Full Date | Check Full Date | ...`

When the run finishes, the status bar tells you how many rows got flagged. A row gets flagged for any of these reasons:

- The original value was vague (`circa 1962`, `before 1991`).
- The app couldn't recognize the format.
- The original cell contained multiple values separated by semicolons.
- The result didn't match a strict `MM/DD/YYYY` or `MM/DD/YYYY - MM/DD/YYYY` shape.

Flagged rows aren't errors — they're invitations to glance at the row and decide what to do.

---

## Special outputs you might see

These show up when the input expressed something more nuanced than a plain date or range. They are always flagged for review.

| Output | What it means |
|--------|---------------|
| `undated` | The original said "n.d.", "no date", "not dated", etc. |
| `circa 1962` | The original said "circa 1962", "ca. 1962", "approx. 1962", etc. |
| `before 01/01/1991` | The original said "before 1991", "pre-1991", or "ante 1991". |
| `before 10/15/1991` | The original gave a specific cutoff date and asked for "before" that date. |
| `after 12/31/1991` | The original said "after 1991" or "post-1991". |
| `after 10/15/1991` | The original gave a specific date and asked for "after" that date. |

For year-only inputs, "before" lands on **January 1** of that year (a tight bound — anything before that point excludes the year itself). "After" lands on **December 31**, with the same logic.

---

## What gets cleaned vs. what stays the same

### Always cleaned (regardless of mode)

These archival ID columns get their leading zeros restored on every save, no matter which mode you picked:

| Column header (any variant works) | Format |
|-----------------------------------|--------|
| `RG`, `Record Group Number` | Exactly 4 digits — `200` becomes `0200`, `9200` stays `9200`. |
| `SG`, `SubGr`, `SubGroup`, `Subgroup Number` | Exactly 3 characters — `22` becomes `022`, `W22` stays `W22`, single-letter prefix preserved. |
| `Series`, `Series Number` | Same as SG. |
| `SubSeries Number` | Same as SG. |

### Left alone

Every other column in your spreadsheet — Folder Number, Sequential Box Number, Title, Description, Container Barcode, anything else — is preserved exactly as it appeared in the source. Leading zeros stay, codes like `001.001` stay, no surprises.

---

## Patterns the app recognizes

The conversion engine tries many input formats. Here are the most common ones you'll encounter, grouped by type. (For the full, code-accurate parsing order, see `CONVERSIONS.md`.)

### Already-formatted dates

| Input | Output |
|-------|--------|
| `05/31/1964` | `05/31/1964` |
| `01/01/1962 - 12/31/1962` | `01/01/1962 - 12/31/1962` |
| `5/8/2026` | `05/08/2026` (leading zeros added) |

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
| `Jun-62` | `06/01/1962 - 06/30/1962` (2-digit year auto-expanded) |
| `June 5, 1964` | `06/05/1964` |
| `June 5th, 1964` | `06/05/1964` |

### Month and year ranges

| Input | Output |
|-------|--------|
| `June 1, 1962 - August 5, 1964` | `06/01/1962 - 08/05/1964` |
| `June 1 - 5 1962` | `06/01/1962 - 06/05/1962` |
| `1962/06 - 1962/08` | `06/01/1962 - 08/31/1962` |

### ISO / Dublin Core formats (best handled in Dublin Core mode)

| Input | Output |
|-------|--------|
| `2026-05-08` | `05/08/2026` |
| `2026-05-08 14:30:00` | `05/08/2026` (time portion dropped) |
| `1962-06/1965-08` | `06/01/1962 - 08/31/1965` |
| `1962-06-05/1965-08-12` | `06/05/1962 - 08/12/1965` |

### Fuzzy / approximate dates (always flagged)

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
| `n.d.` / `N.D.` / `no date` / `undated` | `undated` |

### Wildcards and incomplete inputs

| Input | Output |
|-------|--------|
| `06/??/1962` | `06/01/1962 - 06/30/1962` |
| `06/00/1962` | `06/01/1962 - 06/30/1962` |
| `?? - 10/15/1991` | `before 10/15/1991` |
| `10/15/1991 - ??` | `after 10/15/1991` |

### Excel serial numbers (sometimes pasted from old workbooks)

| Input | Output |
|-------|--------|
| `44197` | `01/01/2021` (decoded from Excel's internal date number) |

### Inputs the app doesn't recognize

If the app sees something it doesn't have a pattern for, it leaves the value as-is and sets the `Check` column to `Yes`. Examples:

| Input | Output | Check |
|-------|--------|-------|
| `Spring 1962` | `Spring 1962` | Yes |
| `Easter 1964` | `Easter 1964` | Yes |
| Any free-text comment | passed through | Yes |

This is intentional — better to flag than to guess wrong.

---

## If something goes wrong

### The app shows an error dialog

Click OK. The app keeps a log file at `%TEMP%\date-formatter.log` (your system's temp folder). Open it in Notepad to see what happened. Share that log with your IT Admin if you need help.

### "File in use" prompt

Close the spreadsheet in Excel (or whatever has it open) and click Retry.

### The app won't open at all

This usually means Python isn't installed or the script path moved. Contact your IT Admin.

### A row got flagged that shouldn't have

Check the `Original_` column — that's the raw value the app saw. If it was an unusual format the app doesn't know, you have two options: clean up the source value and re-run, or just edit the formatted column directly to whatever is correct.

---

## Tips and good practices

- **Always make a backup copy of your spreadsheet before running.** The app overwrites your file in place.
- Run on **one column at a time** until you're comfortable with the output, then batch larger jobs.
- After a run, **sort by the `Check` column** to bring all flagged rows to the top — much faster than scanning the whole sheet.
- The app handles `.xlsx` and `.csv`. If your file is in `.xls` (old format), save it as `.xlsx` first.
- Light mode and dark mode are both fine for your eyes — pick whichever you prefer. Your choice is remembered.

---

## Need help?

Contact your IT Admin or whoever provided this app. Include the log file from `%TEMP%\date-formatter.log` if you ran into a specific error — that file has the technical details they'll need.
