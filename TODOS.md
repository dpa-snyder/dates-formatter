# TODOs

Ongoing and pinned items. See ACTION-PLAN.md for completed work.

---

## P0 — Bug Fixes (identified from test output analysis)

These are confirmed bugs with wrong or garbled output. Highest priority.

---
- `convert_strange_named_ranges` does not fully normalize named month ranges when only one side includes a year (example: `June 1 1940 - July 2`). Current behavior should remain flagged (`Check ... = Yes`) until parser logic is fixed.

---

## Next Phase

### GUI
Polish and package the GUI app for end users. Potential future work:
- friendlier output naming and save-location controls
- bundled Windows packaging if Python should not be installed separately
- clearer help text for mode selection and flagged rows

---

## Housekeeping

### Suppress openpyxl deprecation warning during tests
`openpyxl` emits a Python 3.13 deprecation warning (`datetime.utcnow()`) during fixture reads. Current workaround is to suppress it in the test command.
