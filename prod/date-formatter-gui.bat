@echo off

REM ─────────────────────────────────────────────────────────────────────────────
REM  Date Formatter — GUI Launcher
REM  Requires: Python 3.x, customtkinter, pandas, openpyxl
REM  Install deps (run once): pip install customtkinter pandas openpyxl
REM
REM  Drop gui.py into %USERPROFILE%\scripts\ then double-click this bat to launch.
REM ─────────────────────────────────────────────────────────────────────────────

python "%USERPROFILE%\scripts\gui.py"

REM If Python exits with an error (e.g. missing dependency), hold the window
REM open so the user can read the message before it disappears.
if %errorlevel% neq 0 (
    echo.
    echo ERROR: the script exited with code %errorlevel%.
    echo Check that Python is installed and dependencies are up to date:
    echo   pip install customtkinter pandas openpyxl
    echo.
    pause
)
