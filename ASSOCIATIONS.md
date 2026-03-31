# Launcher Associations

Maps the Windows launcher to the deployed GUI app and its in-app conversion modes.

---

## date-formatter-gui.bat
**Script:** `prod/gui.py`
**Deployed to:** `%USERPROFILE%\scripts\gui.py`
**Launcher path:** `%USERPROFILE%\scripts\date-formatter-gui.bat`
**Purpose:** Starts the GUI app that exposes all three conversion modes in one place

---

## In-App Modes
**Single Date Conversion:** strict single-date output — `MM/DD/YYYY`
**ArchivERA Conversion:** normalized range output — `MM/DD/YYYY - MM/DD/YYYY`
**DublinCore Conversion:** converts common non-DC inputs into Dublin Core-friendly date output

---

## Column Output (all three modes)

After running any script, the chosen column and its companions appear in this order:

| Column | Description |
|--------|-------------|
| `{chosen column}` | Formatted date (replaces original value in-place) |
| `Original_{chosen column}` | Raw original value for review |
| `Check {chosen column}` | Flagged `Yes` if output needs manual review |
