# Conversion Reference

Documents every input pattern the script recognizes for each of the three modes, **in the order the parser tries them**. First match wins.

Common conventions:
- **Output column** = `MM/DD/YYYY` or `MM/DD/YYYY - MM/DD/YYYY` or a descriptive token (`undated`, `circa YYYY`, `before MM/DD/YYYY`, `after MM/DD/YYYY`).
- **Check column** = `Yes` when the row needs a human review (ambiguous, descriptive, or unrecognized). Blank otherwise.
- **Year-only inputs** are usually expanded into full ranges.
- Parenthetical content (`"... (circa)"`) is stripped before matching in all modes.
- Single-digit month/day are zero-padded before matching (`1/5/1991` → `01/05/1991`).

---

## Mode 1 — Single Date Conversion

Output: `MM/DD/YYYY`. The pipeline first runs the full **Date Range** parser (Mode 2), then collapses any resulting range to its **start date**.

| # | Step | Behavior |
|---|------|----------|
| 1 | Empty / undated keywords (`undated`, `n.d.`, `nd`, `n d`, `no date`) | Output: `""` (empty) |
| 2 | Run **Date Range** pipeline (Mode 2) | See below |
| 3 | If result contains ` - ` | Keep portion before the dash |
| 4 | If result matches `MM/DD/YYYY` | Use as-is |
| 5 | Anything else | Output: `""` |

Check column: `Yes` if output is **not** `MM/DD/YYYY`. Blank otherwise.

### Examples

| Input | Output | Check |
|-------|--------|-------|
| `5/8/2026` | `05/08/2026` | |
| `05/31/1964` | `05/31/1964` | |
| `01/01/1962 - 12/31/1962` | `01/01/1962` | |
| `1962` | `01/01/1962` | |
| `June 5, 1964` | `06/05/1964` | |
| `Jun 1964` | `06/01/1964` | |
| `1960s` | `01/01/1960` | |
| `circa 1962` | `""` | Yes |
| `before 1991` | `""` | Yes |
| `undated` | `""` | Yes |
| `n.d.` | `""` | Yes |
| garbage / unrecognized | `""` | Yes |

---

## Mode 2 — ArchivERA / Date Range Conversion

Output: `MM/DD/YYYY - MM/DD/YYYY` for ranges, `MM/DD/YYYY` for single dates, or descriptive tokens (`undated`, `circa YYYY`, `before MM/DD/YYYY`, `after MM/DD/YYYY`).

Parser tries each step in this order; first match wins.

| # | Pattern | Example input | Example output | Check |
|---|---------|---------------|----------------|-------|
| 0a | Strip parens — `... (anything) ...` removed | `1962 (uncertain)` | (continues parsing as `1962`) | |
| 0b | Zero-pad month/day to 2 digits | `1/5/1991` | (continues as `01/05/1991`) | |
| 1 | Already-formatted range `MM/DD/YYYY - MM/DD/YYYY` | `01/01/1962 - 12/31/1962` | `01/01/1962 - 12/31/1962` | |
| 2 | 4-digit year (1000–2100) | `1962` | `01/01/1962 - 12/31/1962` | |
| 3 | Excel serial (5-digit number) | `44197` | `01/01/2021` | Yes |
| 4 | Year list separated by `, ; -` or whitespace, 2+ years | `1962, 1965, 1971` | `01/01/1962 - 12/31/1971` | Yes |
| 5 | `MonthName D, YYYY - MonthName D, YYYY` (any month length) | `June 1, 1962 - August 5, 1964` | `06/01/1962 - 08/05/1964` | |
| 6 | Same with comma+dash variant | `Jun 1, 1962 - Aug 5, 1964` | `06/01/1962 - 08/05/1964` | |
| 7 | `MonthName YYYY` (month + year only) | `June 1962` | `06/01/1962 - 06/30/1962` | |
| 8 | `MonthName Dst, YYYY` (ordinal day) | `June 5th, 1964` | `06/05/1964` | |
| 9 | `YYYY vol` / `YYYY volume` | `1962 vol 3` | `01/01/1962 - 12/31/1962` | Yes |
| 10 | No-date markers (`N.D.`, `U.D.`, `No Date`, `not dated`) | `N.D.` | `undated` | |
| 11 | Excel serial range `NNNNN - NNNNN` (either side optional) | `44197 - 44561` | `01/01/2021 - 12/31/2021` | |
| 12 | ISO `YYYY-MM-DD` | `1962-06-05` | `06/05/1962` | |
| 13 | **`before` / `pre` / `ante` / `after` / `post` + year or full date** | `before 1991` | `before 01/01/1991` | Yes |
| 13 | (same) | `before 10/15/1991` | `before 10/15/1991` | Yes |
| 13 | (same) | `pre-1991` | `before 01/01/1991` | Yes |
| 13 | (same) | `after 1991` | `after 12/31/1991` | Yes |
| 13 | (same) | `post-10/15/1991` | `after 10/15/1991` | Yes |
| 14 | ISO timestamp `YYYY-MM-DD HH:MM:SS` | `1962-06-05 14:30:00` | `06/05/1962` | |
| 15 | `YYYY - YYYY` year range | `1962 - 1965` | `01/01/1962 - 12/31/1965` | |
| 16 | `YYYY/MM - YYYY/MM` | `1962/06 - 1962/08` | `06/01/1962 - 08/31/1962` | |
| 17 | Decade shorthand `YYYY-YY` (e.g. `1962-65`) | `1962-65` | `01/01/1962 - 12/31/1965` | |
| 18 | `?? - MM/DD/YYYY`, `?? - YYYY`, `MM/DD/YYYY - ??` | `?? - 10/15/1991` | `before 10/15/1991` | Yes |
| 19 | `M/00/YYYY - M/00/YYYY` (zero days) | `06/00/1962 - 08/00/1962` | `06/01/1962 - 08/31/1962` | |
| 20 | `M/00/YYYY` (single, zero day) | `06/00/1962` | `06/01/1962 - 06/30/1962` | |
| 21 | `M//YYYY` (double slash) | `6//1962` | `06/01/1962 - 06/30/1962` | |
| 22 | Range containing `??` or `00` somewhere | `06/??/1962 - 08/??/1962` | `06/01/1962 - 08/31/1962` | |
| 23 | Plain `MM/DD/YYYY` | `06/05/1962` | `06/05/1962` | |
| 24 | `circa` / `cir` / `ca` / `approx` / `c.` + year | `circa 1962` | `circa 1962` | Yes |
| 25 | Decade `YYYYs` / explicit decade range / lone year (revisit) | `1960s` | `01/01/1960 - 12/31/1969` | |
| 26 | `??` wildcards (e.g. `06/??/1962`) | `06/??/1962` | `06/01/1962 - 06/30/1962` | |
| 27 | `MonthName YYYY` (case-insensitive, abbreviations) | `Jun 1962` | `06/01/1962 - 06/30/1962` | |
| 28 | `MonthName-YY` (2-digit year, 50+ → 19YY, else 20YY) | `Jun-62` | `06/01/1962 - 06/30/1962` | |
| 29 | `Month D - D YYYY` (single month, day range) | `June 1 - 5 1962` | `06/01/1962 - 06/05/1962` | |
| 30 | **Fallthrough** — pattern not matched | `Spring 1962` | `Spring 1962` (unchanged) | Yes |

### Post-processing (all rows)

After the per-row parser runs, the column gets two clean-up passes:

1. **`convert_strange_named_ranges`** — handles non-standard month-name ranges like `Jun 1 - Aug 5 1962`.
2. **`ensure_chronological_order`** — if a range comes out reversed (`12/31/1965 - 01/01/1962`), it gets swapped.

Then `is_valid_date_format` decides the Check value:
- `Yes` if output is **not** `MM/DD/YYYY`, **not** `MM/DD/YYYY - MM/DD/YYYY`, and **not** `undated`.
- Also `Yes` if the original input contained `;` (likely a multi-value field).

---

## Mode 3 — Dublin Core Conversion

Output: same as Mode 2 (DC-style date strings), but the parser knows additional ISO/DC input formats.

| # | Pattern | Example input | Example output |
|---|---------|---------------|----------------|
| 0 | Already `MM/DD/YYYY - MM/DD/YYYY` | `01/01/1962 - 12/31/1962` | unchanged |
| 0a | Strip parens | `1962 (approx)` | (continues as `1962`) |
| 1 | Excel serial (5-digit) | `44197` | `01/01/2021` |
| 2 | Excel serial range | `44197 - 44561` | `01/01/2021 - 12/31/2021` |
| 3 | No-date markers | `n.d.` | `undated` |
| 4 | ISO timestamp `YYYY-MM-DD HH:MM:SS` | `1962-06-05 14:30:00` | `06/05/1962` |
| 5 | ISO `YYYY-MM-DD` | `1962-06-05` | `06/05/1962` |
| 6 | DC range `YYYY-YYYY` | `1962-1965` | `01/01/1962 - 12/31/1965` |
| 7 | DC partial `YYYY/YYYY-MM` | `1962/1965-08` | `01/01/1962 - 08/31/1965` |
| 8 | DC partial `YYYY-MM/YYYY` | `1962-06/1965` | `06/01/1962 - 12/31/1965` |
| 9 | DC partial `YYYY-MM/YYYY-MM` | `1962-06/1965-08` | `06/01/1962 - 08/31/1965` |
| 10 | DC year list `YYYY/YYYY[/YYYY...]` | `1962/1965/1971` | `01/01/1962 - 12/31/1971` |
| 11 | ISO range `YYYY-MM-DD/YYYY-MM-DD` | `1962-06-05/1965-08-12` | `06/05/1962 - 08/12/1965` |
| 12 | DC `YYYY-MM` (month) or `YYYY-YY` (decade) | `1962-06` / `1962-65` | `06/01/1962 - 06/30/1962` / `01/01/1962 - 12/31/1965` |
| 13 | DC year `YYYY` | `1962` | `01/01/1962 - 12/31/1962` |
| 14 | Mixed `MM-DD-YYYY/YYYY-MM-DD` | `06-05-1962/1965-08-12` | `06/05/1962 - 08/12/1965` |
| 15 | ISO range with `to` literal (`... TO ...`) | `1962-06-05 TO 1965-08-12` | recurses → `06/05/1962 - 08/12/1965` |
| 16 | **`before` / `pre` / `ante` / `after` / `post` + year or full date** | `before 1991` | `before 01/01/1991` |
| 16 | (same) | `after 10/15/1991` | `after 10/15/1991` |
| 17 | `circa` family | `circa 1962` | `circa 1962` |
| 18 | `MonthName YYYY` | `June 1962` | `06/01/1962 - 06/30/1962` |
| 19 | `M/00/YYYY` | `06/00/1962` | `06/01/1962 - 06/30/1962` |
| 20 | **Fallthrough** — unmatched | `Spring 1962` | `Spring 1962` (unchanged) |

Dublin Core mode does **not** apply `convert_strange_named_ranges` or chronological order swap. Check column flags any output that doesn't match `MM/DD/YYYY` / range / `undated`.

---

## Always-applied column normalization

Runs on **every** save (regardless of mode), only on these recognized columns:

| Column (any of) | Target width | Letter prefix allowed? |
|-----------------|--------------|------------------------|
| `RG`, `Record Group Number` | 4 chars | No |
| `SG`, `SubGr`, `SubGroup`, `Subgroup Number` | 3 chars | Yes (single leading letter) |
| `Series`, `Series Number` | 3 chars | Yes (single leading letter) |
| `SubSeries Number` | 3 chars | Yes (single leading letter) |

Examples:

| Column | Input | Output |
|--------|-------|--------|
| RG | `9200` | `9200` |
| RG | `200` | `0200` |
| RG | `42` | `0042` |
| SG | `W22` | `W22` |
| SG | `W2` | `W02` |
| SG | `22` | `022` |
| SG | `W` | `W` (no digits — passed through) |
| Any | empty | empty |
| Any | unknown shape (e.g. `12A`, `W2X`) | unchanged (no crash) |

**All other columns** (Folder Number, Sequential Box Number, Title, etc.) are read as text and saved as text — leading zeros preserved, no numeric coercion.
