# Dates Formatter

Desktop app for normalizing inconsistent date formats in Excel and CSV spreadsheets. Built for archival and records-management workflows where source date fields may be exact, fuzzy, partial, ISO/Dublin Core-shaped, or ambiguous.

## Current release

Latest public release: `v0.2.9`, keyboard shortcuts, Settings dialog, and all-platform desktop packages.

Release page:

```text
https://github.com/dpa-snyder/dates-formatter/releases/latest
```

| Platform | Asset | Notes |
|----------|-------|-------|
| Windows | `date-formatter-v0.2.9-windows-amd64.exe` | Standalone Wails desktop app. Public downloads may trigger browser or SmartScreen trust prompts. |
| macOS | `date-formatter-v0.2.9-macos-arm64.zip` | Apple silicon app bundle. Public downloads may trigger Gatekeeper trust prompts. |
| Linux | `date-formatter-v0.2.9-linux-amd64.deb` | Debian/Ubuntu-family package with GTK/WebKitGTK runtime dependencies. |
| Linux | `date-formatter-v0.2.9-linux-x86_64.rpm` | Fedora/RHEL-family package with GTK/WebKitGTK runtime dependencies. |
| Linux | `date-formatter-v0.2.9-linux-amd64.tar.gz` | Portable fallback archive. Install GTK3 and WebKitGTK 4.1 runtime packages manually if needed. |

Public GitHub downloads may not yet be recognized as trusted publisher builds by Windows, macOS, Linux desktop environments, or your browser. Enterprise environments may receive signed or managed builds through IT. In that case, launch behavior may differ from public GitHub downloads.

## App modes

The app provides three conversion options in one interface.

| Mode | Output | Use case |
|------|--------|----------|
| Single Date | `MM/DD/YYYY` | Records that should resolve to a single normalized date. |
| ArchivEra | `MM/DD/YYYY - MM/DD/YYYY` | Records that should resolve to a normalized date range. |
| Dublin Core | Normal single-date or range output from ISO/DC inputs | Mixed inputs with Dublin Core or ISO 8601-style dates. |

## YY prefix override

Two-digit years stay ambiguous unless the user resolves them.

| Input | Setting | Output | Check |
|-------|---------|--------|-------|
| `5/29/26` | YY prefix off | `05/29/26` | `Yes` |
| `Jun-62` | YY prefix off | `06/01/62 - 06/30/62` | `Yes` |
| `5/29/26` | YY prefix `18` | `05/29/1826` | blank |
| `Jun-62` | YY prefix `18` | `06/01/1862 - 06/30/1862` | blank |

No automatic century pivot is used for historical data.

## Output guarantees

Every formatted output respects these invariants.

* Days per month follow the calendar. The app does not emit generated values like `02/30/1990` or `04/31/1990`.
* February 29 only appears in valid leap years.
* In any output range `start - end`, the start date is on or before the end date.
* Excel serial values match Excel's displayed date, including the 1900 leap-year quirk.

Invalid input dates are not corrected. They are passed through unchanged and flagged for review.

## Column output

After running any mode, three columns appear together in the spreadsheet.

| Column | Description |
|--------|-------------|
| `{chosen column}` | Formatted date output. Replaces the original value in place. |
| `Original_{chosen column}` | Original raw value preserved for review. |
| `Check {chosen column}` | `Yes` if the output needs manual review. |

The Wails app can overwrite the original file or write a sibling `-formatted` copy.

## Documentation

| Document | Purpose |
|----------|---------|
| `MANUAL.md` and `user-manual.html` | End-user guide. Must stay current with app behavior and release assets. |
| `CONVERSIONS.md` | Technical reference. Per-mode input/output tables in parser order. |
| `TODOS.md` | Active task list. |
| `DONE.md` | Completed work archive. |
| `index.html` | GitHub Pages dashboard. Must stay current before commits and pushes. |
| `AGENTS.md` | Repo-local working rules for future agents. |

## Structure

```text
wails-app/                     # Current desktop app, Wails + React + Go
  dateengine/                  # Pure Go date conversion engine
  frontend/public/user-manual.html
  build/bin/date-formatter.app # Local macOS build output, ignored when untracked

prod/                          # Legacy Python deploy-staging scripts
  date-formatter-gui.py
  date-formatter-gui.bat
  user-manual.html

src/                           # Legacy Python development copy
  date-formatter-gui.py
  user-manual.html

tests/                         # Python unittest fixtures
test-files/                    # Sample spreadsheets

.github/workflows/             # GitHub Actions release builds
index.html                     # Project dashboard
requirements.txt               # Legacy Python dependencies
```

## Build and test

Use Nix packages first when possible.

Python tests:

```bash
./run-tests.sh
```

Go tests:

```bash
cd wails-app
GOCACHE=/tmp/dates-formatter-go-build go test ./...
```

Frontend build:

```bash
cd wails-app/frontend
npm run build
```

Wails build examples:

```bash
cd wails-app
nix shell nixpkgs#wails -c wails build -clean -o date-formatter -ldflags "-X 'main.version=v0.2.9'"
```

Linux package builds are automated in GitHub Actions with nFPM. Tagged releases publish `.deb`, `.rpm`, and `.tar.gz` assets.

## Release notes

Before committing or pushing app changes:

* Update `MANUAL.md` and all `user-manual.html` copies if behavior, launch steps, warnings, or release assets changed.
* Update `index.html` dashboard so public project state is current.
* Keep `README.md`, `TODOS.md`, and `DONE.md` aligned with the same change.
* Protect secrets. Do not include local tokens, credentials, or private spreadsheet data.
