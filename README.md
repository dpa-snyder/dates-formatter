# Dates Formatter

Desktop app for normalizing inconsistent date formats in Excel and CSV spreadsheets. Built for archival and records-management workflows where source date fields may be exact, fuzzy, partial, ISO/Dublin Core-shaped, or ambiguous.

## Current release

Latest public release: `v0.2.15`, an update-smoke release for Windows managed updates, normal Windows asset naming, and EXE version metadata.

Release page:

```text
https://github.com/dpa-snyder/dates-formatter/releases/latest
```

| Platform | Asset | Notes |
|----------|-------|-------|
| Windows | `date-formatter.exe` | Standalone Wails desktop app with EXE version metadata. Public downloads may trigger browser or SmartScreen trust prompts. |
| macOS | `date-formatter-v0.2.15-macos-arm64.zip` | Apple silicon app bundle. Public downloads may trigger Gatekeeper trust prompts. |
| Linux | `date-formatter-v0.2.15-linux-amd64.deb` | Debian/Ubuntu-family package with GTK/WebKitGTK runtime dependencies. |
| Linux | `date-formatter-v0.2.15-linux-x86_64.rpm` | Fedora/RHEL-family package with GTK/WebKitGTK runtime dependencies. |
| Linux | `date-formatter-v0.2.15-linux-amd64.tar.gz` | Portable fallback archive. Install GTK3 and WebKitGTK 4.1 runtime packages manually if needed. |

Public GitHub downloads may not yet be recognized as trusted publisher builds by Windows, macOS, Linux desktop environments, or your browser. Enterprise environments may receive signed or managed builds through IT. In that case, launch behavior may differ from public GitHub downloads.

## Windows managed updates

Windows users can set an update path in Settings. The default is `X:\Apps\date-formatter.exe`. Folder paths are also supported, as long as the folder contains a single `date-formatter.exe`.

On launch, the app checks that EXE's version metadata against its own version. If the shared EXE is newer, the app silently stages it in the user's local cache and prompts for restart. The restart launches a temporary helper, exits the app, replaces the current EXE, restarts the app, and removes the staged update files.

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

The Wails app can overwrite the original file or write a sibling `-formatted` copy. Overwrite runs write a temporary file first, then replace the target only after the output is complete. If a platform cannot replace in place, the app uses a short-lived backup during the swap.

If a spreadsheet has duplicate or blank headers, the Wails app makes them unique before display and output. For example, duplicate `Date` headers appear as `Date` and `Date (2)`.

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

## Nix development shell (macOS)

Run these commands from the repository root. Nix must be installed with flakes
and `nix-command` enabled. `flake.lock` pins the toolchain; `requirements-dev.lock`
pins Python dependencies and their download hashes. The shell supports Apple
silicon and Intel Macs; only Apple silicon has been tested locally.

The shell provides Python 3.12, Tkinter, and uv. Python 3.12 preserves compatibility with the pinned pandas 2.2.2 dependency. This shell covers the legacy Python app; the Wails frontend keeps its separate shell under `wails-app/frontend`.

### First setup

```bash
cd ~/code/leading-zeros-dates
nix develop
bash scripts/setup-dev.sh
```

The first run downloads the Nix tools and Python packages. Setup creates a separate
`.venv-nix`, leaving any existing `.venv` untouched. Run setup again after pulling
changes to the dependency lock. Entering the shell itself does not install packages,
load `.env`, or run the application.

### Run the application

Inside the shell:

```bash
python src/date-formatter-gui.py
```

### Checks

```bash
./run-tests.sh
```

For a single command without entering an interactive shell:

```bash
nix develop --command bash scripts/setup-dev.sh
nix develop --command ./run-tests.sh
```

Exit the interactive shell with `exit` or Ctrl-D. On later visits, run
`nix develop` from this directory; the existing `.venv-nix` is selected automatically.
Do not activate the older `.venv` inside the Nix shell.

### Optional automatic activation

With direnv installed and hooked into your shell, run `direnv allow` once from
this directory. The checked-in `.envrc` loads the same Nix shell when you enter
the directory and unloads it when you leave. Run `bash scripts/setup-dev.sh`
inside the activated directory for first setup and dependency changes.

### Updating the development environment

Change `requirements.txt` or `pyproject.toml` as appropriate, then run inside the shell:

```bash
uv pip compile requirements.txt \
  --python "$DEV_SHELL_PYTHON" --python-platform aarch64-apple-darwin \
  --generate-hashes --output-file requirements-dev.lock \
  --custom-compile-command 'See README.md: Updating the development environment'
bash scripts/setup-dev.sh
```

Add `--upgrade` to deliberately refresh already locked versions. Use
`nix flake update nixpkgs` to update the Nix toolchain, exit, and enter the shell
again. If setup reports that Nix Python changed, move `.venv-nix` aside to a
backup name and rerun setup. Review lockfile changes and rerun the checks.

### Rollback and platform limits

To return to the old environment, exit the Nix shell (or run `direnv deny` and
leave/re-enter the directory), then run `source .venv/bin/activate`, if that
environment existed before migration and its original interpreter is still installed.
Brew cleanup on the MacBook removed Python 3.13; the preserved old venv directories
are therefore archival, not runnable fallbacks. Use this project’s Nix shell. To
roll back a future Nix update, retain the previous lockfiles and `.venv-nix`,
restore them together, and re-enter the pinned shell. `.venv-nix` requires the Nix
shell's environment, including its Tkinter path where applicable.

This shell is for local macOS development. Windows setup and release packaging
remain separate workflows; Linux is not declared by this flake.

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
GOCACHE=/tmp/dates-formatter-go-build go vet ./...
```

Frontend build:

```bash
cd wails-app/frontend
npm run build
npm audit --audit-level=moderate
```

Wails build examples:

```bash
cd wails-app
nix shell nixpkgs#wails -c wails build -clean -o date-formatter -ldflags "-X 'main.version=v0.2.15'"
```

Linux package builds are automated in GitHub Actions with nFPM. Tagged releases publish `.deb`, `.rpm`, and `.tar.gz` assets.

## Release notes

Before committing or pushing app changes:

* Update `MANUAL.md` and all `user-manual.html` copies if behavior, launch steps, warnings, or release assets changed.
* Update `index.html` dashboard so public project state is current.
* Keep `README.md`, `TODOS.md`, and `DONE.md` aligned with the same change.
* Protect secrets. Do not include local tokens, credentials, or private spreadsheet data.
