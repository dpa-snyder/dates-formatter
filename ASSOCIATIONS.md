# Launcher Associations

Maps the Windows launcher to the deployed GUI app and its in-app conversion modes.

## date-formatter-gui.bat

* **Script:** `prod/date-formatter-gui.py`
* **Companion file:** `prod/user-manual.html` (must live in the same folder as the script)
* **Deployed to:** `%USERPROFILE%\scripts\date-formatter-gui.py` and `%USERPROFILE%\scripts\user-manual.html`
* **Launcher path:** `%USERPROFILE%\scripts\date-formatter-gui.bat` (can also be placed on the Desktop)
* **Purpose:** Starts the GUI app that exposes all three conversion modes in one place.

## In-app modes

* **Single Date Conversion:** strict single-date output `MM/DD/YYYY`.
* **ArchivERA Conversion:** normalized range output `MM/DD/YYYY - MM/DD/YYYY`.
* **Dublin Core Conversion:** converts common non-DC inputs into Dublin Core-friendly date output.

## Column output (all three modes)

After running any mode, the chosen column and its companions appear in this order.

| Column | Description |
|--------|-------------|
| `{chosen column}` | Formatted date. Replaces original value in place. |
| `Original_{chosen column}` | Raw original value for review. |
| `Check {chosen column}` | Flagged `Yes` if output needs manual review. |

## Runtime files created next to the script

| File | Purpose |
|------|---------|
| `dates-formatter-settings.json` | Stores the user's theme preference (`dark` or `light`). Created on first theme toggle. |
| `%TEMP%\date-formatter.log` | Diagnostic log written on every run. Lives in the system temp folder, not next to the script. |
