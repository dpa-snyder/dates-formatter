package dateengine

import (
	"path/filepath"
	"runtime"
	"testing"

	"github.com/xuri/excelize/v2"
)

// fixturesDir returns the path to the shared test-files directory.
func fixturesDir() string {
	_, file, _, _ := runtime.Caller(0)
	return filepath.Join(filepath.Dir(file), "..", "..", "test-files")
}

func loadFixture(t *testing.T, name string) *excelize.File {
	t.Helper()
	f, err := excelize.OpenFile(filepath.Join(fixturesDir(), name))
	if err != nil {
		t.Fatalf("open fixture %s: %v", name, err)
	}
	return f
}

func cellStr(f *excelize.File, sheet, cell string) string {
	v, _ := f.GetCellValue(sheet, cell)
	return v
}

// colIndex maps A=1, B=2, ... for building cell addresses.
func cellAddr(col, row int) string {
	name, _ := excelize.ColumnNumberToName(col)
	return name + toString(row)
}

func toString(n int) string {
	return string(rune('0'+n%10)) // quick hack — replace with strconv.Itoa
}

// ── Utility unit tests (implemented now) ─────────────────────────────────────

func TestGetLastDayOfMonth(t *testing.T) {
	cases := []struct{ year, month, want int }{
		{2000, 2, 29}, // leap year
		{1900, 2, 28}, // not a leap year (century not /400)
		{2001, 2, 28},
		{2000, 1, 31},
		{2000, 4, 30},
		{2000, 12, 31},
	}
	for _, c := range cases {
		if got := GetLastDayOfMonth(c.year, c.month); got != c.want {
			t.Errorf("GetLastDayOfMonth(%d,%d) = %d, want %d", c.year, c.month, got, c.want)
		}
	}
}

func TestExcelSerialToDate(t *testing.T) {
	cases := []struct {
		serial int
		want   string
	}{
		{44197, "01/01/2021"},
		{40178, "12/31/2009"}, // D-022 regression: dual-base fix
		{1,     "01/01/1900"},
	}
	for _, c := range cases {
		if got := ExcelSerialToDate(c.serial); got != c.want {
			t.Errorf("ExcelSerialToDate(%d) = %q, want %q", c.serial, got, c.want)
		}
	}
}

func TestPadAlnum(t *testing.T) {
	cases := []struct{ val string; width int; want string }{
		{"200",  4, "0200"},
		{"9200", 4, "9200"},
		{"22",   3, "022"},
		{"W22",  3, "W22"},
		{"W2",   3, "W02"},
		{"",     4, ""},
		{"12A",  3, "12A"}, // unrecognized shape — pass through
	}
	for _, c := range cases {
		if got := PadAlnum(c.val, c.width); got != c.want {
			t.Errorf("PadAlnum(%q,%d) = %q, want %q", c.val, c.width, got, c.want)
		}
	}
}

func TestIsPlausibleYearText(t *testing.T) {
	if !IsPlausibleYearText("1962") { t.Error("1962 should be plausible") }
	if !IsPlausibleYearText("2026") { t.Error("2026 should be plausible") }
	if IsPlausibleYearText("44197") { t.Error("44197 should not be plausible year") }
	if IsPlausibleYearText("abc")   { t.Error("abc should not be plausible year") }
}

// ── Fixture-driven tests (will pass once Phase 2 engine is implemented) ──────

func TestAEAllRows(t *testing.T) {
	t.Skip("Phase 2 — engine not yet implemented")
}

func TestDCAllRows(t *testing.T) {
	t.Skip("Phase 2 — engine not yet implemented")
}

func TestStrangeRangeAllRows(t *testing.T) {
	t.Skip("Phase 2 — engine not yet implemented")
}

func TestWWIIAllRows(t *testing.T) {
	t.Skip("Phase 2 — engine not yet implemented")
}
