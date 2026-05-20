// Package dateengine implements the date parsing and formatting logic for
// the Date Formatter app. It is a pure Go port of the Python conversion
// pipeline in src/date-formatter-gui.py.
//
// All functions are safe for concurrent use. ConvertMany uses a goroutine
// pool for parallel row processing.
package dateengine

import (
	"fmt"
	"strconv"
	"strings"
	"time"
	"unicode"
)

// Mode selects which conversion pipeline to use.
type Mode int

const (
	ModeSingle Mode = iota // format_single_date
	ModeAE                 // custom_format_date (ArchivEra range)
	ModeDC                 // convert_date_pattern (Dublin Core)
)

// Result holds the converted value and a flag indicating manual review needed.
type Result struct {
	Value   string
	Flagged bool
}

// Convert applies the given mode to a single input string.
func Convert(input string, mode Mode) Result {
	s := strings.TrimSpace(input)
	switch mode {
	case ModeSingle:
		v := FormatSingleDate(s)
		return Result{Value: v, Flagged: v == ""}
	case ModeAE:
		v, flagged := CustomFormatDate(s)
		v = ConvertStrangeNamedRanges(v)
		v = EnsureChronologicalOrder(v)
		return Result{Value: v, Flagged: flagged}
	case ModeDC:
		v := ConvertDatePattern(s)
		v = EnsureChronologicalOrder(v)
		return Result{Value: v, Flagged: isNonStandard(v)}
	}
	return Result{Value: input}
}

// ConvertMany processes a slice of inputs concurrently using a worker pool.
// Results are returned in the same order as inputs.
func ConvertMany(inputs []string, mode Mode) []Result {
	results := make([]Result, len(inputs))
	// TODO Phase 2: implement worker pool
	for i, v := range inputs {
		results[i] = Convert(v, mode)
	}
	return results
}

// ── Public pipeline functions (stubs — Phase 2 fills these in) ────────────────

// FormatSingleDate converts input to a single MM/DD/YYYY date.
// Returns "" for values that cannot be resolved to a single date.
func FormatSingleDate(input string) string {
	// TODO Phase 2
	_ = input
	return ""
}

// CustomFormatDate converts input using the ArchivEra range pipeline.
// Returns (formatted, flagged).
func CustomFormatDate(input string) (string, bool) {
	// TODO Phase 2
	return input, false
}

// ConvertDatePattern converts input using the Dublin Core pipeline.
func ConvertDatePattern(input string) string {
	// TODO Phase 2
	return input
}

// ConvertStrangeNamedRanges handles named month ranges not covered by the
// main pipelines (e.g. "Feb 1 2000 - Feb 29 2000").
func ConvertStrangeNamedRanges(input string) string {
	// TODO Phase 2
	return input
}

// EnsureChronologicalOrder swaps start/end if they are in reverse order.
func EnsureChronologicalOrder(input string) string {
	// TODO Phase 2
	return input
}

// ── Utility functions (implemented now — needed by Phase 3 even before Phase 2) ─

// GetLastDayOfMonth returns the last day of the given month in the given year,
// accounting for leap years.
func GetLastDayOfMonth(year, month int) int {
	return time.Date(year, time.Month(month+1), 0, 0, 0, 0, 0, time.UTC).Day()
}

// ExcelSerialToDate converts an Excel date serial number to MM/DD/YYYY.
// Handles the Excel 1900 leap-year bug (serial < 60 uses base 1899-12-31;
// serial >= 60 uses base 1899-12-30).
func ExcelSerialToDate(serial int) string {
	var base time.Time
	if serial < 60 {
		base = time.Date(1899, 12, 31, 0, 0, 0, 0, time.UTC)
	} else {
		base = time.Date(1899, 12, 30, 0, 0, 0, 0, time.UTC)
	}
	d := base.AddDate(0, 0, serial)
	return fmt.Sprintf("%02d/%02d/%04d", d.Month(), d.Day(), d.Year())
}

// PadAlnum pads a value to the given width. Pure-numeric values are
// zero-padded; values with a single leading letter have their digit portion
// padded; other shapes are returned unchanged.
func PadAlnum(val string, width int) string {
	val = strings.TrimSpace(val)
	if val == "" {
		return val
	}
	// Pure numeric
	if isAllDigits(val) {
		if len(val) < width {
			return strings.Repeat("0", width-len(val)) + val
		}
		return val
	}
	// Single leading letter + digits
	if len(val) >= 2 && unicode.IsLetter(rune(val[0])) && isAllDigits(val[1:]) {
		digits := val[1:]
		target := width - 1
		if len(digits) < target {
			digits = strings.Repeat("0", target-len(digits)) + digits
		}
		return string(val[0]) + digits
	}
	return val
}

// IsPlausibleYearText returns true if s looks like a standalone 4-digit year
// in the range 1000–2999.
func IsPlausibleYearText(s string) bool {
	if len(s) != 4 {
		return false
	}
	n, err := strconv.Atoi(s)
	if err != nil {
		return false
	}
	return n >= 1000 && n <= 2999
}

// IsExcelSerialText returns true if s looks like an Excel date serial
// (5-digit number in the plausible range 1–2958465).
func IsExcelSerialText(s string) bool {
	if len(s) < 4 || len(s) > 6 {
		return false
	}
	n, err := strconv.Atoi(s)
	if err != nil {
		return false
	}
	return n >= 1 && n <= 2958465 && !IsPlausibleYearText(s)
}

// ── Internal helpers ──────────────────────────────────────────────────────────

func isAllDigits(s string) bool {
	for _, c := range s {
		if !unicode.IsDigit(c) {
			return false
		}
	}
	return len(s) > 0
}

func isNonStandard(v string) bool {
	if v == "" || v == "undated" {
		return true
	}
	if strings.HasPrefix(v, "circa ") || strings.HasPrefix(v, "before ") || strings.HasPrefix(v, "after ") {
		return true
	}
	return false
}
