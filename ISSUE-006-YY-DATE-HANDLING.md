# Issue 6: 2-digit year dates should normalize, but stay flagged unless resolved

GitHub issue: [#6](https://github.com/dpa-snyder/dates-formatter/issues/6)

## Summary

The Windows 11 executable showed a case where the first date did not convert when the input used a 2-digit year, for example `5/29/26`.

That input is ambiguous because `26` could mean `1926` or `2026` depending on context. The formatter should still normalize the value, but it should also flag the row for manual review.

## Required behavior

When the formatter sees a date with a 2-digit year:

- Normalize month and day while preserving `YY`
- Mark the row's `Check ...` column as `Yes`
- Leave the original value available for review in the output columns

If the user enables the YY prefix override:

- Require a user-entered 2-digit prefix, such as `15`, `18`, `19`, or `20`
- Convert `YY` to `{prefix}YY`
- Leave `Check ...` blank for that ambiguity because the user resolved it

No automatic century pivot is safe for historical data.

## Examples

- `5/29/26` → `05/29/26` and `Check ... = Yes`
- `5/29/80` → `05/29/80` and `Check ... = Yes`
- `5/29/00` → `05/29/00` and `Check ... = Yes`
- `5/29/26` with prefix `18` → `05/29/1826` and blank `Check ...`

## Test coverage to add

Add regression tests for the 2-digit year path so the formatter does not silently miss it again.

Suggested cases:

- single-date mode with `mm/dd/yy`
- range mode with `mm/dd/yy`
- Dublin Core / ArchivERA paths if they share the same date parser

The important assertion is not only the converted date, but also that the row is flagged for review.

## Notes

This issue is not about changing the intended output format. The output should still be normalized to the repo’s standard `MM/DD/YYYY` shape.

The change is about handling ambiguous user-entered dates safely, not about silently guessing.
