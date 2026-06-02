# Date Formatter Wails App

Current desktop app for Dates Formatter. Frontend is React/TypeScript. Backend is Go with a pure Go date engine in `dateengine/`.

## Features

* Single Date, ArchivEra, and Dublin Core conversion modes.
* Drag/drop or native file picker for `.xlsx` and `.csv`.
* Date-column auto-detection with preselected columns.
* YY prefix override for ambiguous two-digit years.
* Overwrite or save `-formatted` copy.
* Recent files, run progress, cancel, open file, open folder.
* Embedded user manual at `frontend/public/user-manual.html`.

## Development

Use Nix packages first when possible.

```bash
nix shell nixpkgs#wails nixpkgs#go nixpkgs#nodejs_20
wails dev
```

Wails also starts a browser-accessible dev server at `http://localhost:34115` when running in dev mode.

## Test

```bash
GOCACHE=/tmp/dates-formatter-go-build go test ./...
cd frontend
npm run build
```

## Build

Release builds inject the app version into `main.version`.

```bash
wails build -clean -o date-formatter -ldflags "-X 'main.version=v0.2.7'"
```

Windows release build in GitHub Actions uses:

```bash
wails build -platform windows/amd64 -clean -webview2 download -o date-formatter.exe -ldflags "-X 'main.version=$tag'"
```

macOS arm64 local build uses:

```bash
wails build -platform darwin/arm64 -clean -o date-formatter -ldflags "-X 'main.version=v0.2.7'"
```

## Signing status

Public GitHub downloads may not yet be recognized as trusted publisher builds by Windows, macOS, or your browser.

* Windows users may see browser warnings and SmartScreen "Unknown publisher" prompts.
* macOS users may need Control-click, Open, or an allowed quarantine removal command.
* Enterprise builds may be signed or managed by IT and may not show these prompts.

Keep `../MANUAL.md`, `../user-manual.html`, and `frontend/public/user-manual.html` current whenever launch behavior, release assets, or app behavior changes.
