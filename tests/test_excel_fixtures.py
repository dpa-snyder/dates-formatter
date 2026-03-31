import importlib.util
import math
from pathlib import Path
import unittest
import warnings

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "test-files"
GUI_PATH = ROOT / "src" / "gui.py"

warnings.simplefilter("ignore", DeprecationWarning)


def load_gui_module():
    spec = importlib.util.spec_from_file_location("date_formatter_gui", GUI_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


GUI = load_gui_module()


def workbook_row(filename, excel_row_number):
    df = pd.read_excel(FIXTURES / filename)
    return df.iloc[excel_row_number - 2]


def cell_text(value):
    if value is None:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""
    return str(value)


def parse_single_windows(raw_value):
    return GUI.format_single_date(cell_text(raw_value))


def parse_range_windows(raw_value):
    formatted, _flag = GUI.custom_format_date(cell_text(raw_value))
    formatted = GUI.convert_strange_named_ranges(formatted)
    return GUI.ensure_chronological_order(formatted)


def parse_dublin_core(raw_value):
    return GUI.ensure_chronological_order(GUI.convert_date_pattern(cell_text(raw_value)))


class TestFixtureSmoke(unittest.TestCase):
    def test_single_mode_uses_root_fixture_rows(self):
        cases = [
            ("testing-column.xlsx", 46, "Convert Us", "Expected Result"),
            ("testing-column.xlsx", 47, "Convert Us", "Expected Result"),
            ("testing-column.xlsx", 48, "Convert Us", "Expected Result"),
            ("testing-column.xlsx", 49, "Convert Us", "Expected Result"),
        ]
        for filename, rownum, input_col, expected_col in cases:
            row = workbook_row(filename, rownum)
            with self.subTest(file=filename, row=rownum, raw=cell_text(row[input_col])):
                self.assertEqual(
                    parse_single_windows(row[input_col]),
                    cell_text(row[expected_col]),
                )

    def test_range_mode_uses_testing_workbook_rows(self):
        cases = [
            ("testing-column.xlsx", 7),
            ("testing-column.xlsx", 13),
            ("testing-column.xlsx", 25),
            ("testing-column.xlsx", 122),
        ]
        for filename, rownum in cases:
            row = workbook_row(filename, rownum)
            raw = row["Convert Us"]
            with self.subTest(file=filename, row=rownum, raw=cell_text(raw)):
                self.assertEqual(
                    parse_range_windows(raw),
                    cell_text(row["Expected Result"]),
                )

    def test_dublin_core_preserves_known_good_rows(self):
        cases = [7, 8, 9, 10, 11, 12, 25, 30, 46, 59, 77, 122]
        for rownum in cases:
            row = workbook_row("testing-column.xlsx", rownum)
            raw = row["Convert Us"]
            with self.subTest(row=rownum, raw=cell_text(raw)):
                self.assertEqual(
                    parse_dublin_core(raw),
                    cell_text(row["Expected Result"]),
                )

    def test_dublin_core_wwii_fixture_single_dates(self):
        cases = [4, 101, 202, 352, 502]
        for rownum in cases:
            row = workbook_row("dubline-core-test-WWII-dates.xlsx", rownum)
            raw = row["Date Original (Cdm)"]
            with self.subTest(row=rownum, raw=cell_text(raw)):
                self.assertEqual(
                    parse_dublin_core(raw),
                    cell_text(row["DC-FormattedDate Original (Cdm)"]),
                )

    def test_dublin_core_wwii_fixture_date_ranges(self):
        cases = [2, 3, 9]
        for rownum in cases:
            row = workbook_row("dubline-core-test-WWII-dates.xlsx", rownum)
            raw = row["Date Original (Cdm)"]
            with self.subTest(row=rownum, raw=cell_text(raw)):
                self.assertEqual(
                    parse_dublin_core(raw),
                    cell_text(row["DC-FormattedDate Original (Cdm)"]),
                )

    def test_strange_named_ranges_from_root_fixture(self):
        cases = [3, 4, 5, 6]
        for rownum in cases:
            row = workbook_row("strange-range-test.xlsx", rownum)
            raw = row["FullDate"]
            with self.subTest(row=rownum, raw=cell_text(raw)):
                self.assertEqual(
                    GUI.convert_strange_named_ranges(cell_text(raw)),
                    cell_text(row["ExpectedFFD"]),
                )


class TestKnownBugRegressions(unittest.TestCase):
    def test_single_mode_should_not_treat_year_only_values_as_excel_serials(self):
        self.assertEqual(parse_single_windows("1900"), "01/01/1900")
        self.assertEqual(parse_single_windows("1980"), "01/01/1980")

    def test_range_parenthetical_content_should_not_corrupt_output(self):
        row = workbook_row("testing-column.xlsx", 42)
        self.assertEqual(
            parse_range_windows(row["Convert Us"]),
            cell_text(row["Expected Result"]),
        )

    def test_range_zero_day_should_expand_to_full_month(self):
        row = workbook_row("testing-column.xlsx", 102)
        self.assertEqual(
            parse_range_windows(row["Convert Us"]),
            cell_text(row["Expected Result"]),
        )

    def test_range_serial_40178_should_match_fixture_expectation(self):
        row = workbook_row("testing-column.xlsx", 45)
        self.assertEqual(
            parse_range_windows(row["Convert Us"]),
            cell_text(row["Expected Result"]),
        )

    def test_dublin_core_abbreviated_year_range_should_expand_cleanly(self):
        row = workbook_row("testing-column.xlsx", 25)
        self.assertEqual(
            parse_dublin_core(row["Convert Us"]),
            cell_text(row["Expected Result"]),
        )

    def test_dublin_core_out_of_order_ranges_should_be_reordered(self):
        row = workbook_row("testing-column.xlsx", 77)
        self.assertEqual(
            parse_dublin_core(row["Convert Us"]),
            cell_text(row["Expected Result"]),
        )

    def test_dublin_core_month_name_year_should_convert_to_month_range(self):
        row = workbook_row("testing-column.xlsx", 122)
        self.assertEqual(
            parse_dublin_core(row["Convert Us"]),
            cell_text(row["Expected Result"]),
        )


if __name__ == "__main__":
    unittest.main()
