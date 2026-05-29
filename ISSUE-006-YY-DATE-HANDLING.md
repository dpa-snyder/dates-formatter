# Issue 6: 2-digit year dates should convert, but stay flagged for review

GitHub issue: [#6](https://github.com/dpa-snyder/dates-formatter/issues/6)

## Summary

The Windows 11 executable showed a case where the first date did not convert when the input used a 2-digit year, for example `5/29/26`.

That input is ambiguous because `26` could mean `1926` or `2026` depending on context. The formatter should still normalize the value, but it should also flag the row for manual review.

## Required behavior

When the formatter sees a date with a 2-digit year:

- Convert `YY` to `YYYY`
- Mark the row's `Check ...` column as `Yes`
- Leave the original value available for review in the output columns

## Recommended year expansion rule

Use a simple century pivot:

- `00` through `29` → `2000` through `2029`
- `30` through `99` → `1930` through `1999`

This matches the common “19xx vs 20xx” ambiguity and gives a predictable conversion path.

## Examples

- `5/29/26` → `05/29/2026` and `Check ... = Yes`
- `5/29/80` → `05/29/1980` and `Check ... = Yes`
- `5/29/00` → `05/29/2000` and `Check ... = Yes`

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
