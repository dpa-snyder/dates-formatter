# Associations and Launchers

Maps Date Formatter launchers, release assets, companion files, and output behavior.

## Current Wails desktop app

### Windows public release

* **Asset:** `date-formatter.exe`
* **Release page:** `https://github.com/dpa-snyder/dates-formatter/releases/latest`
* **Purpose:** Standalone desktop app with all conversion modes.
* **Signing status:** Public build is currently unsigned. Browsers and Windows SmartScreen may warn that it is unknown or potentially dangerous. Continue only for the official release or an IT-provided build.

### macOS public release

* **Asset:** `date-formatter-v0.2.7-macos-arm64.zip`
* **Contents:** `date-formatter.app`
* **Purpose:** Apple silicon macOS desktop app with all conversion modes.
* **Trust prompts:** Public GitHub downloads may not yet be recognized as trusted publisher builds by macOS. Gatekeeper may require Control-click, Open, or an IT-approved quarantine removal step.

### Enterprise release

Enterprise environments may receive signed or managed builds through IT. Those builds may launch without public-download warning prompts.

## Legacy Python launcher

### date-formatter-gui.bat

* **Target script:** `prod/date-formatter-gui.py`
* **Companion file:** `prod/user-manual.html`
* **Launcher path:** `%USERPROFILE%\scripts\date-formatter-gui.bat` or Desktop shortcut
* **Purpose:** Starts the legacy Python GUI that exposes all three conversion modes in one place.

The Python script and `user-manual.html` must live in the same folder so the in-app manual button can find the HTML file.

## Conversion modes

* **Single Date:** strict single-date output `MM/DD/YYYY`, or unresolved `MM/DD/YY` when two-digit years are preserved for review.
* **ArchivEra:** normalized range output `MM/DD/YYYY - MM/DD/YYYY`, or exact single-date output when the input is exact.
* **Dublin Core:** accepts ISO and Dublin Core-style inputs, then emits normal app output shapes.

## Output columns

All current entry points use the same output column convention.

| Column | Meaning |
|--------|---------|
| `{chosen column}` | Formatted date. Replaces original value in place. |
| `Original_{chosen column}` | Raw original value for review. |
| `Check {chosen column}` | `Yes` if output needs manual review. |

## Output files

| Mode | Behavior |
|------|----------|
| Overwrite | Writes cleaned data back to the source file. |
| Save copy | Writes a sibling file with `-formatted` before the extension. |

Legacy Python deployments may be overwrite-only depending on which script version is installed.

## Diagnostics

| Surface | Location |
|---------|----------|
| Wails settings | Windows: `%APPDATA%\date-formatter\settings.json`; macOS: `~/Library/Application Support/date-formatter/settings.json`. |
| Legacy Python settings | `dates-formatter-settings.json` next to the Python script. |
| Legacy Python log | `%TEMP%\date-formatter.log`. |
| User manual | Built into Wails app; also shipped as `user-manual.html` for docs and legacy Python. |
