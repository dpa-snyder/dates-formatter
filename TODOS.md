# TODOs

Ongoing and pinned items. See ACTION-PLAN.md for completed work.

---

## Pinned

### govserv bat/script name mismatch
`govserv-date-converter.bat` deploys as `gov-serv-date-formatter.py` but the prod script is named `date-formatter-range.py`. Needs to be reconciled — either rename the prod script or update the bat.
> Tracked in ASSOCIATIONS.md as well.

---

## Next Phase

### GUI
Build a graphical interface for the scripts so users don't need to interact with the column-selection dropdown via tkinter. Details TBD.

---

## Housekeeping

### Venv at root
`.venc/` was moved from `prod/` to repo root. Activation scripts inside have stale paths. Rebuild with:
```
python -m venv .venc
pip install -r requirements.txt
```

### test-scripts/ is now empty
Directory exists but has no contents after cleanup. Can be removed or repopulated with actual tests.
