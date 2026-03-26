# Script Associations

Maps each Windows batch launcher to its corresponding Python script and output behavior.

---

## AE-ranged-date-converter.bat
**Script:** `prod/date-formatter-single.py`
**Deployed to:** `%USERPROFILE%\scripts\date-formatter-single.py`
**Output format:** Strict single date — `MM/DD/YYYY`
**Use case:** Records with a single date value per row

---

## dublin-core-date-converter.bat
**Script:** `prod/dublin-core-date-convert.py`
**Deployed to:** `%USERPROFILE%\scripts\dublin-core-date-convert.py`
**Output format:** Dublin Core compatible — `MM/DD/YYYY` or `MM/DD/YYYY - MM/DD/YYYY`
**Use case:** Records using Dublin Core date format conventions

---

## govserv-date-converter.bat
**Script:** `prod/date-formatter-range.py`
**Deployed to:** `%USERPROFILE%\scripts\gov-serv-date-formatter.py`
**Output format:** Date range — `MM/DD/YYYY - MM/DD/YYYY`
**Use case:** Government services records with date ranges

> **TODO:** Bat deploys as `gov-serv-date-formatter.py` but prod script is named `date-formatter-range.py`. Either rename the prod script or update the bat to match.

---

## Column Output (all three scripts)

After running any script, the chosen column and its companions appear in this order:

| Column | Description |
|--------|-------------|
| `{chosen column}` | Formatted date (replaces original value in-place) |
| `Original_{chosen column}` | Raw original value for review |
| `Check {chosen column}` | Flagged `Yes` if output needs manual review |
