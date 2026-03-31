# TODOs

Ongoing and pinned items. See ACTION-PLAN.md for completed work.

---

## P0 — Bug Fixes (identified from test output analysis)

These are confirmed bugs with wrong or garbled output. Highest priority.

---
No open P0 parser bugs are currently tracked in the GUI deployment path. The root fixture suite is passing.

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
