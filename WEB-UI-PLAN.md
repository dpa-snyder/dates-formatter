# Web UI Migration Plan

Replace CustomTkinter GUI with Flask + browser-based UI. Business logic stays in Python; browser is the render surface only. PyInstaller bundling (T-010) is out of scope — tracked separately.

**Target platforms:** Windows + Mac  
**Port strategy:** Auto-pick available port at launch  
**Guiding rule:** No behavioral changes to date logic. All processing goes through `date_engine.py`. Flask routes are thin wrappers only.

---

## Phases

| Phase | Goal | Risk |
|-------|------|------|
| 1 | Extract logic | Medium — careful surgery on 1980-line file |
| 2 | Flask backend | Low — standard CRUD endpoints |
| 3 | Frontend | Low — no logic here |
| 4 | Launcher | Low — port + process management |
| 5 | Parity + polish | Low — feature catch-up |
| SB | Stretch: PyWebView | Medium — platform WebView2 dependency |

---

## Phase 1: Logic Extraction

**Goal:** Isolate all date parsing and formatting into a pure Python module. No UI imports. Tests pass before and after. This phase is a prerequisite for everything else and must be completed in isolation.

| ID | Order | Title | Notes |
|----|-------|-------|-------|
| W-101 | 1 | Audit `date-formatter-gui.py` | Identify every pure-logic function (date parsing, formatting, conversion, validation) vs every UI function. Document the boundary. |
| W-102 | 2 | Create `date_engine.py` | Extract all pure logic into `prod/date_engine.py`. No `customtkinter`, no `tkinter`, no `threading` GUI calls. Module must be importable with no side effects. |
| W-103 | 3 | Repoint existing GUI to engine | Update `prod/date-formatter-gui.py` to `from date_engine import ...`. Existing CTk GUI must still run and behave identically. |
| W-104 | 4 | Run full test suite | `./run-tests.sh`. All tests must pass. No regressions. If any fail, fix before proceeding. |

---

## Phase 2: Flask Backend

**Goal:** HTTP API layer that wraps `date_engine`. Routes do no processing themselves — they validate inputs, call the engine, and return results.

| ID | Order | Title | Notes |
|----|-------|-------|-------|
| W-201 | 1 | Scaffold `web/app.py` | Flask app. Blueprint structure if routes grow. Config: debug off, host `127.0.0.1` only (no LAN exposure). |
| W-202 | 2 | `POST /api/load` | Accept file upload (xlsx or csv). Save to temp dir. Return: column names, row count, file token (UUID mapped to temp path server-side). |
| W-203 | 3 | `POST /api/process` | Accept: file token, column name, mode (`single`/`ae`/`dublin`), output mode (`overwrite`/`copy`). Call engine. Return processed file as download. Clean temp files after response. |
| W-204 | 4 | `GET /api/settings` | Return current settings JSON. |
| W-205 | 5 | `POST /api/settings` | Write updated settings JSON. Same keys as existing `dates-formatter-settings.json`. |
| W-206 | 6 | `GET /manual` | Serve `user-manual.html` from `prod/`. |
| W-207 | 7 | Error handling | All routes return JSON errors with `{"error": "..."}` and appropriate HTTP status. No Flask HTML error pages. |

**Temp file strategy:** Each upload gets a UUID. Server keeps a dict `{uuid: temp_path}`. File deleted after `/api/process` streams the response. Orphaned temp files cleaned on next startup.

---

## Phase 3: Frontend

**Goal:** Single-page app at `index.html`. Vanilla JS (no framework). Clean, native-feeling design — not a data tool aesthetic.

| ID | Order | Title | Notes |
|----|-------|-------|-------|
| W-301 | 1 | Design system + base template | `web/templates/index.html`. CSS custom properties for color/spacing. Dark/light mode via `data-theme` attribute. Matches existing color palette (`#235194` blue, `#e5842a` orange from `index.html`). |
| W-302 | 2 | File upload zone | Drag-and-drop target + click-to-browse fallback. Shows filename, row count, column count after load. Calls `/api/load`. |
| W-303 | 3 | Column picker | Dropdown populated from `/api/load` response. Shows column names. |
| W-304 | 4 | Mode selector + options | Three modes (Single / AE / Dublin Core). Per-mode description text. Output mode toggle (overwrite / copy). |
| W-305 | 5 | Run + progress + download | Run button → spinner → `/api/process` → triggers browser download of result file. Status text shows row count processed. |
| W-306 | 6 | Settings panel | Accessible via gear icon. Theme toggle (dark/light). Output mode default. Persisted via `/api/settings`. |
| W-307 | 7 | Error states | File format errors, bad column, engine errors. Displayed inline, not alert dialogs. |
| W-308 | 8 | User manual link | Button/link that opens `/manual` in new tab. |

**JS strategy:** Fetch API for all calls. No jQuery. No bundler. Single `app.js` file. Keep it simple — this is a utility, not a dashboard.

---

## Phase 4: Launcher

**Goal:** Single entry point that starts Flask, finds a free port, opens the browser, and handles shutdown cleanly on both platforms.

| ID | Order | Title | Notes |
|----|-------|-------|-------|
| W-401 | 1 | `launch.py` | Find free port via `socket.bind(('', 0))`. Start Flask in a daemon thread. Wait for server ready (poll `GET /`). Open `http://127.0.0.1:{port}` in default browser. Block on `KeyboardInterrupt` (Ctrl+C). |
| W-402 | 2 | Windows launcher | `prod/date-formatter-web.bat`. Calls `py launch.py`. Keep old `.bat` for CTk GUI until Phase 5 complete. |
| W-403 | 3 | Mac launcher | `prod/date-formatter-web.command` (double-clickable shell script on Mac). `chmod +x` required. |
| W-404 | 4 | Shutdown behavior | On `KeyboardInterrupt` or browser window close signal: clean temp dir, exit. Browser window close is best-effort (JS `beforeunload` → `POST /api/shutdown`). |

---

## Phase 5: Parity + Polish

**Goal:** Feature parity with CTk GUI, plus improvements unlocked by the web stack.

| ID | Order | Title | Notes |
|----|-------|-------|-------|
| W-501 | 1 | Theme persistence | On load, `GET /api/settings` → set `data-theme`. Toggle saves via `POST /api/settings`. |
| W-502 | 2 | Recent files | Store last 5 file names in settings. Show in a "recent" list under the upload zone. Click re-opens browse dialog (can't restore path — browser security). |
| W-503 | 3 | Column auto-detection (T-013) | After `/api/load`, add a `date_columns` list to response (columns where majority of values match a date pattern). Highlight these in the picker. |
| W-504 | 4 | Keyboard shortcuts | `Ctrl/Cmd+O` → open file browse. `Ctrl/Cmd+R` → run. `Ctrl/Cmd+,` → open settings. `Ctrl/Cmd+?` → open manual. Implemented in `app.js`. |
| W-505 | 5 | Smoke test (both platforms) | End-to-end: launch → load `9200-W22.xlsx` → pick column → run → verify output. Windows + Mac. |
| W-506 | 6 | Retire CTk GUI (optional) | Once Web UI is validated on client machine, CTk GUI can be archived. Keep until T-001 is confirmed done. |

---

## Stretch B: PyWebView (Option B)

**Goal:** Wrap the Flask app in a native webview window — no browser chrome, no URL bar, dedicated app window. Same HTML/CSS/JS frontend, same Flask backend.

**Dependency:** `pywebview>=4.4`. Uses Edge WebView2 on Windows (present on Win11 and modern Win10), WebKit on Mac.

**Risk:** Edge WebView2 not guaranteed on older Windows installs. Must document fallback (use browser launcher instead).

| ID | Order | Title | Notes |
|----|-------|-------|-------|
| W-SB1 | 1 | Add `pywebview` to `requirements.txt` | Pin to `>=4.4`. Verify install on both platforms. |
| W-SB2 | 2 | `launch_native.py` | Start Flask in background thread. Open pywebview window at `http://127.0.0.1:{port}`. Window title: "Dates Formatter". Fixed size or resizable (decide). `webview.start()` blocks until window closed → clean shutdown. |
| W-SB3 | 3 | Native launchers | `date-formatter-native.bat` (Windows), `date-formatter-native.command` (Mac). |
| W-SB4 | 4 | Platform test | Windows: confirm Edge WebView2 renders correctly. Mac: confirm WebKit renders correctly. Flag any CSS/JS differences. |
| W-SB5 | 5 | Fallback doc | If WebView2 not installed on Windows, document fallback: run `date-formatter-web.bat` instead (browser version). |

---

## File layout (post-migration)

```text
prod/
  date_engine.py              ← extracted logic (new, Phase 1)
  date-formatter-gui.py       ← existing CTk GUI, now imports from engine
  launch.py                   ← web launcher (new, Phase 4)
  launch_native.py            ← PyWebView launcher (new, Stretch B)
  date-formatter-web.bat      ← Windows web launcher
  date-formatter-web.command  ← Mac web launcher
  date-formatter-gui.bat      ← existing CTk launcher (kept until W-506)
  user-manual.html

web/
  app.py                      ← Flask app
  templates/
    index.html                ← single-page UI
  static/
    app.js
    style.css
```

---

## What does NOT change

- All date parsing logic (patterns, edge cases, error detection)
- All output column structure (`{col}`, `Original_{col}`, `Check {col}`)
- All three conversion modes and their behaviors
- Output file format (xlsx/csv)
- Settings file format and keys
- `user-manual.html` content
- Test suite

---

## Open items / decisions needed

| Item | Default assumption | Flag if wrong |
|------|--------------------|---------------|
| PyInstaller (T-010) | Out of scope for this plan | — |
| CTk GUI retirement | Keep until client smoke test passes (W-505) | — |
| Web framework | Flask (vanilla, no extensions beyond `flask`) | If FastAPI preferred, raise before W-201 |
| JS framework | Vanilla JS, no bundler | If a lightweight framework is preferred, raise before W-301 |
| PyWebView window size | Resizable, min 900×650 | — |
