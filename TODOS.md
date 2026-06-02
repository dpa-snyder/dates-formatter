# TODOs

Indexed active task list. Each task has an **ID**, **Order**, **Importance** (1 = nice-to-have, 5 = critical), and notes.

See `CONVERSIONS.md` for the full input/output spec.
See `DONE.md` for completed work.
See `recommendations.md` for older review notes.

## Active

| ID | Order | Importance | Title | Notes |
|----|-------|------------|-------|-------|
| T-001 | 1 | 4 | Validate `v0.2.7` release in real Windows and macOS environments | Smoke-test public `date-formatter.exe` and `date-formatter-v0.2.7-macos-arm64.zip` with `9200-W22.xlsx`. Confirm browser warnings, SmartScreen, Gatekeeper behavior, YY prefix, overwrite/copy output, date-column auto-detection, and open file/folder actions. Enterprise signed builds may behave differently. |
| T-019 | 2 | 5 | Add public code signing and macOS notarization | Public builds are currently unsigned/not notarized for end-user trust prompts. Windows needs a publisher certificate path. macOS needs Developer ID signing and notarization. Keep enterprise signing separate if IT manages it. |
| T-020 | 3 | 4 | Automate macOS release artifact in GitHub Actions | Windows EXE is built by `.github/workflows/build-windows.yml`. macOS arm64 zip was built locally for `v0.2.7`; add a macOS workflow when signing/notarization path is decided. |
| T-014 | 4 | 2 | Keyboard shortcuts | Bind `Ctrl+O`/`Cmd+O` browse, `Ctrl+R`/`Cmd+R` run, `Ctrl+,`/`Cmd+,` settings, and `Ctrl+/`/`Cmd+/` manual. |
| T-016 | 5 | 2 | Settings dialog | Current Wails app persists theme, palette, recent files, output mode, and YY settings. Add a visible settings dialog only if users need central control for defaults, output folder, log level, or advanced options. |
| T-017 | 6 | 3 | Custom output format options | Let users pick output shape and date order instead of hardcoded `MM/DD/YYYY`: year-first, month-first, day-first, separator choice, range vs single, and 2- vs 4-digit year. Requires a format engine refactor in Go and Python legacy paths. |
| T-021 | 7 | 2 | Triage stale GitHub issues | Open issues #1 through #5 predate the Wails app. Review against current release and close, update, or replace with current release-specific issues. |
