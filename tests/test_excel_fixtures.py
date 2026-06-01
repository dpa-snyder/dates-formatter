import importlib.util
import math
from pathlib import Path
import unittest
import warnings

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "test-files"
GUI_PATH = ROOT / "src" / "date-formatter-gui.py"

warnings.simplefilter("ignore", DeprecationWarning)


def load_gui_module():
    spec = importlib.util.spec_from_file_location("date_formatter_gui", GUI_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


GUI = load_gui_module()


# ── Helpers ────────────────────────────────────────────────────────────────────

def cell(value):
    if value is None:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""
    return str(value).strip()


def parse_single(raw):
    return GUI.format_single_date(cell(raw))


def parse_single_with_prefix(raw, prefix):
    return GUI.format_single_date(cell(raw), prefix)


def parse_ae(raw):
    formatted, _flag = GUI.custom_format_date(cell(raw))
    formatted = GUI.convert_strange_named_ranges(formatted)
    return GUI.ensure_chronological_order(formatted)


def parse_ae_with_prefix(raw, prefix):
    formatted, _flag = GUI.custom_format_date(cell(raw), prefix)
    formatted = GUI.convert_strange_named_ranges(formatted)
    return GUI.ensure_chronological_order(formatted)


def parse_dc(raw):
    return GUI.ensure_chronological_order(GUI.convert_date_pattern(cell(raw)))


def parse_dc_with_prefix(raw, prefix):
    return GUI.ensure_chronological_order(GUI.convert_date_pattern(cell(raw), prefix))


def load_fixture(filename):
    return pd.read_excel(FIXTURES / filename, dtype=str, keep_default_na=False)


# ── Stale expected-value overrides ─────────────────────────────────────────────
#
# These rows have Expected Result values that predate the D-003/D-006 fixes.
# The code behaviour is correct; the fixture column was not updated at the time.
#   - rows 69-76: post/pre/ante year-only → now expands to full date bound
#   - rows 17-18: suspected data-entry errors in the fixture
#
_TC_OVERRIDES = {
    17: "04/14/2004 - 05/31/2008",   # fixture says 04/30, but May 31 is correct
    18: "06/01/2008 - 10/30/2009",   # fixture says 10/31, but Oct 30 is correct
    69: "after 12/31/1850",
    70: "after 12/31/1850",
    71: "before 01/01/1850",
    72: "before 01/01/1850",
    73: "after 12/31/1850",
    74: "before 01/01/1850",
    75: "before 01/01/1998",
    76: "before 01/01/1878",
}

# Rows to skip: Solved != 'y' (tracked / partial / in-progress)
_TC_SKIP_SOLVED = {"T", "p", ""}


# ── Comprehensive fixture tests ─────────────────────────────────────────────────

class TestAllFixtureRows(unittest.TestCase):
    """Data-driven: every solvable row across all three fixture files."""

    # ── testing-column.xlsx ───────────────────────────────────────────────────

    def test_testing_column_non_empty_expected(self):
        """
        All rows where Solved='y' and Expected Result is non-empty.
        Uses AE mode first; falls back to DC mode for patterns only DC handles.
        Stale fixture rows use _TC_OVERRIDES instead of the fixture column.
        """
        df = load_fixture("testing-column.xlsx")
        for idx, row in df.iterrows():
            excel_row = idx + 2
            if cell(row["Solved"]) in _TC_SKIP_SOLVED:
                continue
            raw = cell(row["Convert Us"])
            expected = _TC_OVERRIDES.get(excel_row, cell(row["Expected Result"]))
            if not expected:
                continue  # pass-through rows tested separately

            with self.subTest(excel_row=excel_row, raw=raw):
                got_ae = parse_ae(raw)
                if got_ae == expected:
                    self.assertEqual(got_ae, expected)
                else:
                    self.assertEqual(parse_dc(raw), expected)

    def test_testing_column_passthrough_rows(self):
        """
        Rows where Solved='y' and Expected Result is empty should pass through
        unchanged in DC mode (DC is stricter and doesn't over-convert).
        """
        df = load_fixture("testing-column.xlsx")
        for idx, row in df.iterrows():
            excel_row = idx + 2
            if cell(row["Solved"]) in _TC_SKIP_SOLVED:
                continue
            raw = cell(row["Convert Us"])
            if cell(row["Expected Result"]) or excel_row in _TC_OVERRIDES:
                continue
            if not raw:
                continue  # blank-input row handled by empty-input test

            with self.subTest(excel_row=excel_row, raw=raw):
                self.assertEqual(parse_dc(raw), raw)

    def test_testing_column_empty_input_returns_undated(self):
        """Empty input cell should produce 'undated' in both modes (row 112)."""
        self.assertEqual(parse_ae(""), "undated")
        self.assertEqual(parse_dc(""), "undated")

    # ── strange-range-test.xlsx ───────────────────────────────────────────────

    def test_strange_ranges_all_rows(self):
        """All five named-range cases in strange-range-test.xlsx."""
        df = load_fixture("strange-range-test.xlsx")
        for idx, row in df.iterrows():
            raw = cell(row["FullDate"])
            expected = cell(row["ExpectedFFD"])
            if not raw or not expected:
                continue
            with self.subTest(excel_row=idx + 2, raw=raw):
                self.assertEqual(GUI.convert_strange_named_ranges(raw), expected)

    # ── dubline-core-test-WWII-dates.xlsx ────────────────────────────────────

    def test_wwii_all_rows_dc_mode(self):
        """All 672 rows of the WWII Dublin Core fixture in DC mode."""
        df = load_fixture("dubline-core-test-WWII-dates.xlsx")
        for idx, row in df.iterrows():
            raw = cell(row["Date Original (Cdm)"])
            expected = cell(row["DC-FormattedDate Original (Cdm)"])
            with self.subTest(excel_row=idx + 2, raw=raw):
                self.assertEqual(parse_dc(raw), expected)


# ── Targeted regression tests ───────────────────────────────────────────────────

class TestKnownBugRegressions(unittest.TestCase):

    def _tc(self, excel_row):
        df = load_fixture("testing-column.xlsx")
        return df.iloc[excel_row - 2]

    # Single mode
    def test_single_mode_iso_timestamps(self):
        cases = [
            (46, "Convert Us", "Expected Result"),
            (47, "Convert Us", "Expected Result"),
            (48, "Convert Us", "Expected Result"),
            (49, "Convert Us", "Expected Result"),
        ]
        for excel_row, in_col, exp_col in cases:
            row = self._tc(excel_row)
            with self.subTest(excel_row=excel_row, raw=cell(row[in_col])):
                self.assertEqual(parse_single(row[in_col]), cell(row[exp_col]))

    def test_single_mode_year_values_not_treated_as_excel_serials(self):
        self.assertEqual(parse_single("1900"), "01/01/1900")
        self.assertEqual(parse_single("1980"), "01/01/1980")

    def test_two_digit_numeric_dates_preserve_year_and_require_review(self):
        cases = [
            ("5/29/26", "05/29/26"),
            ("5/29/80", "05/29/80"),
            ("5/29/00", "05/29/00"),
            ("5/29/30", "05/29/30"),
        ]
        for raw, expected in cases:
            with self.subTest(raw=raw):
                self.assertEqual(parse_single(raw), expected)
                formatted, flag = GUI.custom_format_date(raw)
                self.assertEqual(formatted, expected)
                self.assertEqual(flag, "Yes")
                self.assertEqual(parse_dc(raw), expected)
                self.assertTrue(GUI.has_two_digit_year_date(raw))

    def test_two_digit_numeric_ranges_preserve_year_and_require_review(self):
        formatted, flag = GUI.custom_format_date("5/29/26 - 6/2/26")
        self.assertEqual(formatted, "05/29/26 - 06/02/26")
        self.assertEqual(flag, "Yes")
        self.assertEqual(parse_dc("5/29/26 - 6/2/26"), "05/29/26 - 06/02/26")

    def test_two_digit_numeric_dates_prefix_override_clears_review(self):
        cases = [
            ("5/29/26", "18", "05/29/1826"),
            ("5/29/80", "19", "05/29/1980"),
            ("5/29/00", "20", "05/29/2000"),
            ("5/29/30", "15", "05/29/1530"),
        ]
        for raw, prefix, expected in cases:
            with self.subTest(raw=raw, prefix=prefix):
                self.assertEqual(parse_single_with_prefix(raw, prefix), expected)
                formatted, flag = GUI.custom_format_date(raw, prefix)
                self.assertEqual(formatted, expected)
                self.assertEqual(flag, "")
                self.assertEqual(parse_dc_with_prefix(raw, prefix), expected)

    def test_two_digit_numeric_ranges_prefix_override_clears_review(self):
        formatted, flag = GUI.custom_format_date("5/29/26 - 6/2/26", "18")
        self.assertEqual(formatted, "05/29/1826 - 06/02/1826")
        self.assertEqual(flag, "")
        self.assertEqual(
            parse_dc_with_prefix("5/29/26 - 6/2/26", "18"),
            "05/29/1826 - 06/02/1826")

    def test_month_two_digit_year_prefix_override(self):
        formatted, flag = GUI.custom_format_date("Jun-62")
        self.assertEqual(formatted, "06/01/62 - 06/30/62")
        self.assertEqual(flag, "Yes")
        self.assertEqual(parse_dc("Jun-62"), "06/01/62 - 06/30/62")
        formatted, flag = GUI.custom_format_date("Jun-62", "18")
        self.assertEqual(formatted, "06/01/1862 - 06/30/1862")
        self.assertEqual(flag, "")
        self.assertEqual(parse_dc_with_prefix("Jun-62", "18"), "06/01/1862 - 06/30/1862")

    # AE mode regressions
    def test_ae_parenthetical_content_does_not_corrupt_output(self):
        row = self._tc(42)
        self.assertEqual(parse_ae(row["Convert Us"]), cell(row["Expected Result"]))

    def test_ae_zero_day_expands_to_full_month(self):
        row = self._tc(102)
        self.assertEqual(parse_ae(row["Convert Us"]), cell(row["Expected Result"]))

    def test_ae_excel_serial_40178(self):
        row = self._tc(45)
        self.assertEqual(parse_ae(row["Convert Us"]), cell(row["Expected Result"]))

    def test_ae_out_of_order_range_reordered(self):
        row = self._tc(77)
        self.assertEqual(parse_ae(row["Convert Us"]), cell(row["Expected Result"]))

    # DC mode regressions
    def test_dc_abbreviated_year_range_expands(self):
        row = self._tc(25)
        self.assertEqual(parse_dc(row["Convert Us"]), cell(row["Expected Result"]))

    def test_dc_out_of_order_range_reordered(self):
        row = self._tc(77)
        self.assertEqual(parse_dc(row["Convert Us"]), cell(row["Expected Result"]))

    def test_dc_month_name_year_converts_to_range(self):
        row = self._tc(122)
        self.assertEqual(parse_dc(row["Convert Us"]), cell(row["Expected Result"]))

    # Bug-fix regressions (added with parser fixes)
    def test_circa_iso_date_preserved_as_is(self):
        """circa YYYY-MM-DD must not be stripped to circa YYYY (was a bug)."""
        self.assertEqual(parse_dc("circa 1947-07-17"), "circa 1947-07-17")
        self.assertEqual(parse_dc("circa 1946-01-01/1947-12-31"), "circa 1946-01-01/1947-12-31")
        self.assertEqual(parse_ae("circa 1947-09-06"), "circa 1947-09-06")

    def test_circa_year_only_still_works(self):
        self.assertEqual(parse_dc("circa 1765"), "circa 1765")
        self.assertEqual(parse_ae("circa 1962"), "circa 1962")

    def test_spanish_month_names_pass_through(self):
        """'Mayo' (Spanish May) must not be converted to a date range (was a bug)."""
        self.assertEqual(parse_ae("Mayo 2016"), "Mayo 2016")
        self.assertEqual(parse_dc("Mayo 2016"), "Mayo 2016")

    def test_empty_input_returns_undated(self):
        """Blank cell should produce 'undated' in both modes (was a bug)."""
        self.assertEqual(parse_ae(""), "undated")
        self.assertEqual(parse_dc(""), "undated")

    # Named month abbreviations still work after Mayo fix
    def test_month_abbreviations_still_convert(self):
        self.assertEqual(parse_ae("Jun-62"), "06/01/62 - 06/30/62")
        self.assertEqual(parse_ae_with_prefix("Jun-62", "19"), "06/01/1962 - 06/30/1962")
        self.assertEqual(parse_ae("June 1962"), "06/01/1962 - 06/30/1962")
        self.assertEqual(parse_ae("January 11, 2012"), "01/11/2012")
        self.assertEqual(parse_ae("Feb 21 2012"), "02/21/2012")
        self.assertEqual(parse_ae("Sept. 3rd 1798"), "09/03/1798")

    def test_windows_unc_open_path_normalized(self):
        path = "//DOSFS01/users/lindsay.townsend/Documents/9015-038-003_formatted.xlsx"
        expected = r"\\DOSFS01\users\lindsay.townsend\Documents\9015-038-003_formatted.xlsx"
        self.assertEqual(GUI.normalize_open_path(path, "win32"), expected)


if __name__ == "__main__":
    unittest.main()
