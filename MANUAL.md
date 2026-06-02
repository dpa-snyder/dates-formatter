# Date Formatter: User Manual

Guide for using Date Formatter to standardize date columns in Excel and CSV spreadsheets.

## What this app does

Date Formatter reads date-like values from spreadsheet columns and rewrites them in a consistent output format. It is built for archival data where dates may appear as `5/8/2026`, `May 8, 2026`, `2026-05-08`, `circa 2026`, `1960s`, `n.d.`, and similar mixed formats.

Values the app cannot confidently parse are left visible and flagged for review.

## Download and launch

### Enterprise or IT-managed install

If your IT department provided the app, use the shortcut or application they installed. Enterprise builds may be signed and managed, so Windows, macOS, or Linux may open them without extra warning prompts.

### Public GitHub release

Download only from the official GitHub Releases page:

`https://github.com/dpa-snyder/dates-formatter/releases/latest`

The current public release includes:

| Platform | File | Notes |
|----------|------|-------|
| Windows | `date-formatter-v0.2.8-windows-amd64.exe` | Standalone Wails desktop app. |
| macOS | `date-formatter-v0.2.8-macos-arm64.zip` | Apple silicon macOS app bundle. Unzip before launching. |
| Linux | `date-formatter-v0.2.8-linux-amd64.deb` | Debian/Ubuntu-family package. |
| Linux | `date-formatter-v0.2.8-linux-x86_64.rpm` | Fedora/RHEL-family package. |
| Linux | `date-formatter-v0.2.8-linux-amd64.tar.gz` | Portable fallback archive. |

Public GitHub downloads may not yet be recognized as trusted publisher builds by Windows, macOS, Linux desktop environments, or your browser. Enterprise or IT-distributed builds may be signed and managed, and may launch without these warnings. For public downloads, continue only if the file came from the official release page. Do not bypass warnings for copies from email, chat, or an unknown website.

### Windows EXE warnings

After downloading `date-formatter-v0.2.8-windows-amd64.exe`, Chrome or Edge may show a message such as "This file may be dangerous" or "Date Formatter is not commonly downloaded." Choose the browser's keep option only when the file came from the official release page.

On first launch, Windows SmartScreen may show "Windows protected your PC" or "Unknown publisher." Choose **More info**, then **Run anyway**, only for the official release or an IT-provided build.

### macOS app warnings

Download the macOS zip, unzip it, and move `date-formatter.app` to Applications or another normal app folder.

Because the public macOS download may not yet be recognized as a trusted publisher build, macOS may show a message that the app cannot be opened, is from an unidentified developer, or is damaged. First try Control-clicking the app, choosing **Open**, then choosing **Open** again.

If macOS still blocks the app and your IT policy allows it, remove the quarantine flag in Terminal:

```bash
xattr -dr com.apple.quarantine /Applications/date-formatter.app
```

Adjust the path if you placed the app somewhere else.

### Linux package warnings

For Debian or Ubuntu-family systems, download the `.deb` package and install it with your normal package tool, for example:

```bash
sudo apt install ./date-formatter-v0.2.8-linux-amd64.deb
```

For Fedora, RHEL, or compatible systems, download the `.rpm` package and install it with:

```bash
sudo dnf install ./date-formatter-v0.2.8-linux-x86_64.rpm
```

The Linux packages install `date-formatter`, desktop launcher metadata, the app icon, and a copy of this manual. They declare GTK3 and WebKitGTK 4.1 runtime dependencies. If your distro uses different package names, use the `.tar.gz` fallback and install the distro's GTK3 and WebKitGTK runtime packages manually.

For the fallback archive:

```bash
tar -xzf date-formatter-v0.2.8-linux-amd64.tar.gz
cd date-formatter-v0.2.8-linux-amd64
chmod +x date-formatter
./date-formatter
```

### Legacy Python launch

Some older deployments use the Python script instead of the Wails desktop app. In that setup, launch the shortcut named `date-formatter-gui.bat`, or run:

```bat
py %USERPROFILE%\scripts\date-formatter-gui.py
```

The Python script and `user-manual.html` must live in the same folder.

## Window tour

The Wails desktop app has these main areas:

| Area | Purpose |
|------|---------|
| Sidebar | Switch between Converter and User Manual. Change light, dark, or system theme. Pick the color palette. View app version. |
| Conversion Mode | Choose Single Date, ArchivEra, or Dublin Core. |
| File | Drop an `.xlsx` or `.csv` file, browse for one, or reopen a recent file. |
| Date Columns | Pick columns to convert. Date-looking columns are preselected and marked with a `dates` badge. |
| Date Interpretation | Optional YY prefix for ambiguous two-digit years. |
| Output | Choose overwrite or save-copy behavior, then run or cancel. |
| Result | Shows rows processed, flagged rows, output path, and buttons to open the file or folder. |

The legacy Python app has the same core GUI workflow and conversion functionality as the desktop app, including the same conversion modes and YY behavior. Important differences: the Wails desktop app is faster on larger files and is packaged as a normal app or EXE; the Python app may require Python dependencies and can run slower, especially on large spreadsheets.

## Conversion modes

### Single Date

Output: `MM/DD/YYYY`, or `MM/DD/YY` when a two-digit year is preserved for review.

Use this when each row should resolve to one date.

Examples:

| Input | Output |
|-------|--------|
| `5/8/2026` | `05/08/2026` |
| `May 8, 2026` | `05/08/2026` |
| `01/01/1962 - 12/31/1962` | `01/01/1962` |

Vague values such as `circa 1962`, `1960s`, `before 1991`, or `undated` produce an empty value and are flagged.

### ArchivEra

Output: `MM/DD/YYYY - MM/DD/YYYY` for ranges, or `MM/DD/YYYY` for exact single dates.

Use this when each row represents a span of time.

Examples:

| Input | Output |
|-------|--------|
| `1962` | `01/01/1962 - 12/31/1962` |
| `Jun 1962` | `06/01/1962 - 06/30/1962` |
| `1960s` | `01/01/1960 - 12/31/1969` |
| `5/8/2026` | `05/08/2026` |

Fuzzy values are preserved and flagged: `circa 1962`, `before 10/15/1991`, `after 1991`, `undated`.

### Dublin Core

Use this for ISO and Dublin Core input patterns. It accepts all ArchivEra-style inputs plus formats such as `2026-05-08`, `1962-1965`, `1962-06/1965-08`, and `YYYY-MM-DD/YYYY-MM-DD`.

Output still uses the app's normal `MM/DD/YYYY` or range shape.

If unsure, choose **ArchivEra** unless your source data uses ISO or Dublin Core date strings.

## YY prefix feature

Two-digit years are ambiguous in archival data. `5/29/26` might mean 1826, 1926, or 2026 depending on the collection.

Default behavior:

| Input | Output | Check |
|-------|--------|-------|
| `5/29/26` | `05/29/26` | `Yes` |
| `Jun-62` | `06/01/62 - 06/30/62` | `Yes` |

To resolve the century during a run, enable **Use YY prefix** and enter exactly two digits.

| Input | Prefix | Output | Check |
|-------|--------|--------|-------|
| `5/29/26` | `18` | `05/29/1826` | blank |
| `Jun-62` | `18` | `06/01/1862 - 06/30/1862` | blank |
| `5/29/26` | `20` | `05/29/2026` | blank |

The prefix applies only to recognized two-digit year dates. Leave it off when you want those rows preserved and flagged for human review.

## Run workflow

1. Open or drop an `.xlsx` or `.csv` file.
2. Confirm the date columns. The app preselects likely date columns, but you can change the selection.
3. Choose conversion mode.
4. Set YY prefix only if the collection's two-digit year century is known.
5. Choose **Overwrite** or **Save copy**.
6. Click **Run**.

**Overwrite** writes the cleaned data back to the original file.

**Save copy** writes a sibling file named with `-formatted`, such as `records-formatted.xlsx`.

If the source file is open in Excel, close it before overwriting. If a run is taking too long, click **Cancel**.

## Output columns

For every selected column, the app keeps the chosen column name and inserts two review columns next to it.

| Column | Contents |
|--------|----------|
| `{your column}` | Cleaned date output. Replaces the original value in place. |
| `Original_{your column}` | Raw original value. |
| `Check {your column}` | `Yes` if the row needs review. Blank otherwise. |

Single-column example:

```text
... | Full Date | Original_Full Date | Check Full Date | ...
```

Two-column example:

```text
... | Start Date | Original_Start Date | Check Start Date | End Date | Original_End Date | Check End Date | ...
```

Rows are flagged when the source value is vague, unrecognized, ambiguous, contains multiple values separated by semicolons, or produces a non-standard output.

Flagged rows are not failures. They are rows that need a human glance.

## Built-in safeguards

Every formatted output follows these rules:

| Safeguard | Behavior |
|-----------|----------|
| Calendar day counts | The app does not emit invalid generated dates such as `02/30/1990` or `04/31/1990`. |
| Leap years | February 29 appears only in valid leap years. `02/29/2000` is valid. `02/29/1900` is not. |
| Chronological ranges | In any `start - end` range, the start date is on or before the end date. Reversed ranges are swapped. |
| Excel serials | Five-digit Excel serials match Excel's displayed date, including the 1900 leap-year quirk. |

Invalid input dates are not guessed. They pass through and get flagged.

## Special outputs

These outputs are intentionally flagged.

| Output | Meaning |
|--------|---------|
| `undated` | The source said `n.d.`, `no date`, `not dated`, `undated`, etc. |
| `circa 1962` | The source said `circa 1962`, `ca. 1962`, `approx. 1962`, etc. |
| `before 01/01/1991` | The source said `before 1991`, `pre-1991`, or `ante 1991`. |
| `before 10/15/1991` | The source gave a specific cutoff date with "before". |
| `after 12/31/1991` | The source said `after 1991` or `post-1991`. |
| `after 10/15/1991` | The source gave a specific cutoff date with "after". |

For year-only before/after inputs, the app uses a tight bound: `before YYYY` becomes `before 01/01/YYYY`, and `after YYYY` becomes `after 12/31/YYYY`.

## Columns preserved

The app reads and writes spreadsheet values as text to protect leading zeros and archival identifiers.

These columns are always normalized when present:

| Header | Format |
|--------|--------|
| `RG`, `Record Group Number` | Exactly 4 digits. `200` becomes `0200`. |
| `SG`, `SubGr`, `SubGroup`, `Subgroup Number` | Exactly 3 characters. `22` becomes `022`. `W22` stays `W22`. |
| `Series`, `Series Number` | Same as SG. |
| `SubSeries Number` | Same as SG. |

Other columns, including Folder Number, Sequential Box Number, Title, Description, and Container Barcode, are preserved as text.

## Patterns recognized

For the full parser-order reference, see `CONVERSIONS.md`.

Common examples:

| Type | Input | Output |
|------|-------|--------|
| Already formatted | `05/31/1964` | `05/31/1964` |
| Year | `1962` | `01/01/1962 - 12/31/1962` |
| Year range | `1962-1965` | `01/01/1962 - 12/31/1965` |
| Decade | `1960s` | `01/01/1960 - 12/31/1969` |
| Month/year | `June 1962` | `06/01/1962 - 06/30/1962` |
| Full date | `June 5th, 1964` | `06/05/1964` |
| ISO date | `2026-05-08` | `05/08/2026` |
| Dublin Core range | `1962-06/1965-08` | `06/01/1962 - 08/31/1965` |
| Wildcard day | `06/??/1962` | `06/01/1962 - 06/30/1962` |
| Excel serial | `44197` | `01/01/2021` |

Unrecognized values such as `Spring 1962`, `Easter 1964`, or free-text comments pass through and get `Check = Yes`.

## Troubleshooting

| Problem | What to do |
|---------|------------|
| Browser says download may be dangerous | Confirm the file came from the official GitHub release or IT. If not, stop. If yes, use the browser keep option. |
| Windows SmartScreen blocks launch | Use **More info** and **Run anyway** only for the official or IT-provided EXE. |
| macOS blocks launch | Control-click the app and choose **Open**. If allowed by policy, remove quarantine with `xattr -dr com.apple.quarantine /Applications/date-formatter.app`. |
| Linux package will not install | Use the `.deb` on Debian/Ubuntu-family systems or `.rpm` on Fedora/RHEL-family systems. If dependency names do not match your distro, use the `.tar.gz` fallback and install GTK3 plus WebKitGTK manually. |
| File cannot be overwritten | Close Excel or any app using the spreadsheet, then run again. |
| YY prefix error | Enter exactly two digits, such as `15`, `18`, `19`, or `20`, or turn off the YY prefix option. |
| Date columns look wrong | Clear or add column selections manually. Auto-detection is a helper, not a rule. |
| A row was flagged unexpectedly | Check the `Original_` column, then edit the source or output value as needed. |

## Diagnostics

| Item | Wails desktop app | Legacy Python app |
|------|-------------------|-------------------|
| Version | Sidebar footer. Release builds show tags such as `v0.2.8`. | Bottom-left footer, such as `v2026.06.01`. |
| Settings | Windows: `%APPDATA%\date-formatter\settings.json`. macOS: `~/Library/Application Support/date-formatter/settings.json`. Linux: `~/.config/date-formatter/settings.json`. | `dates-formatter-settings.json` next to the Python script. |
| Manual | Built into the app and also shipped as `user-manual.html`. | `user-manual.html` next to the Python script. |
| Logs | Progress and messages appear in the app run panel. | `%TEMP%\date-formatter.log`. |

When reporting a problem, include the app version, operating system, release source, file type, conversion mode, and one or two sample source values.
