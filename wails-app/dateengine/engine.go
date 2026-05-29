// Package dateengine is a pure-Go port of the Python date-parsing pipeline
// in src/date-formatter-gui.py. All public functions are safe for concurrent
// use. ConvertMany uses a goroutine pool for parallel row processing.
package dateengine

import (
	"fmt"
	"regexp"
	"runtime"
	"strconv"
	"strings"
	"sync"
	"time"
	"unicode"
)

// ── Mode ──────────────────────────────────────────────────────────────────────

// Mode selects the conversion pipeline.
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

// ── Entry points ──────────────────────────────────────────────────────────────

// Convert applies the given mode to a single input string.
func Convert(input string, mode Mode) Result {
	s := strings.TrimSpace(input)
	switch mode {
	case ModeSingle:
		v := FormatSingleDate(s)
		return Result{Value: v, Flagged: v == "" || HasTwoDigitYearDate(s)}
	case ModeAE:
		v, flagged := CustomFormatDate(s)
		v = ConvertStrangeNamedRanges(v)
		v = EnsureChronologicalOrder(v)
		return Result{Value: v, Flagged: flagged}
	case ModeDC:
		v := ConvertDatePattern(s)
		v = EnsureChronologicalOrder(v)
		return Result{Value: v, Flagged: isNonStandard(v) || HasTwoDigitYearDate(s)}
	}
	return Result{Value: input}
}

// ConvertMany processes a slice of inputs concurrently using a worker pool.
// Results are returned in the same order as inputs.
func ConvertMany(inputs []string, mode Mode) []Result {
	n := len(inputs)
	if n == 0 {
		return nil
	}
	results := make([]Result, n)
	type job struct {
		idx int
		val string
	}
	jobs := make(chan job, n)
	for i, v := range inputs {
		jobs <- job{i, v}
	}
	close(jobs)

	workers := runtime.GOMAXPROCS(0)
	if workers > n {
		workers = n
	}
	var wg sync.WaitGroup
	wg.Add(workers)
	for range make([]struct{}, workers) {
		go func() {
			defer wg.Done()
			for j := range jobs {
				results[j.idx] = Convert(j.val, mode)
			}
		}()
	}
	wg.Wait()
	return results
}

// ── Month helpers ─────────────────────────────────────────────────────────────

var monthNum = map[string]int{
	"Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
	"Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12,
}

// toMonthNum returns the month number for any English month name or 3-letter
// abbreviation (case-insensitive). Sept maps to Sep (9).
func toMonthNum(s string) (int, bool) {
	if len(s) < 3 {
		return 0, false
	}
	key := strings.ToUpper(s[:1]) + strings.ToLower(s[1:3])
	n, ok := monthNum[key]
	return n, ok
}

// monthList is the alternation used in regexps for month names.
const monthList = `(?i)(January|February|March|April|May|June|July|August|` +
	`September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sept|Sep|Oct|Nov|Dec)`

// ── Compiled regexps ──────────────────────────────────────────────────────────

var (
	// shared
	reFullRange  = regexp.MustCompile(`^\d{2}/\d{2}/\d{4} - \d{2}/\d{2}/\d{4}$`)
	reNoDate     = regexp.MustCompile(`(?i)\b(N\.?\s*D\.?|U\.?\s*D\.?|No\s+Date|not\s+dated|undated|ud)\b`)
	reLeadZero1  = regexp.MustCompile(`\b(\d)/(\d{1,2})/(\d{4})`)
	reLeadZero2  = regexp.MustCompile(`(\d{2})/(\d)/(\d{4})`)
	reParens     = regexp.MustCompile(`\s*\(.*?\)`)
	rePrePost    = regexp.MustCompile(`(?i)\b(before|pre|ante|after|post)\.?\s*-?\s*(\d{1,2}/\d{1,2}/\d{4}|\d{4})\b`)
	reYYDate     = regexp.MustCompile(`^(\d{1,2})([/-])(\d{1,2})([/-])(\d{2})$`)
	reYYDateScan = regexp.MustCompile(`(^|[^0-9])(\d{1,2})([/-])(\d{1,2})([/-])(\d{2})([^0-9]|$)`)

	// AE mode
	reMultiYear           = regexp.MustCompile(`^\d{4}([,;\s\-]+\d{4})+$`)
	reMonthRangeA         = regexp.MustCompile(`^([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})\s+[–\-]\s+([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})`)
	reMonthRangeB         = regexp.MustCompile(`^([A-Za-z]+)\s+(\d{1,2}),\s+(\d{4})\s+-\s+([A-Za-z]+)\s+(\d{1,2}),\s+(\d{4})`)
	reMonthYearAnchor     = regexp.MustCompile(monthList + `\.?\s*(\d{4})$`)
	reMonthDayYear        = regexp.MustCompile(`^` + monthList + `\.?\s*(\d{1,2})(?:st|nd|rd|th)?,?\s*(\d{4})`)
	reVolYear             = regexp.MustCompile(`(?i)^(\d{4})\s+(?:vol|volume)\b`)
	reSerialRange         = regexp.MustCompile(`^(\d{5})?\s*-\s*(\d{5})?$`)
	reISODateAE           = regexp.MustCompile(`^(\d{4})[\-/](\d{1,2})[\-/](\d{1,2})`)
	reISOTimestamp        = regexp.MustCompile(`^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}`)
	reYearRange           = regexp.MustCompile(`^(\d{4})\s*-\s*(\d{4})`)
	reISOMonthSlash       = regexp.MustCompile(`^(\d{4})/(\d{2}) - (\d{4})/(\d{2})`)
	reYYYYMM              = regexp.MustCompile(`^(\d{4})-(\d{2})`)
	reQQBeforeDate        = regexp.MustCompile(`^\?{1,2} - (\d{1,2})/(\d{1,2})/(\d{4})$`)
	reQQBeforeYear        = regexp.MustCompile(`^\?{1,2} - (\d{4})$`)
	reAfterDate           = regexp.MustCompile(`^(\d{1,2})/(\d{1,2})/(\d{4}) - \?{1,2}$`)
	reZeroDayRange        = regexp.MustCompile(`^(\d{1,2})/0+/(\d{4}) - (\d{1,2})/0+/(\d{4})`)
	reZeroDay             = regexp.MustCompile(`^(\d{1,2})/0+/(\d{4})`)
	reDoubleSlash         = regexp.MustCompile(`^(\d{1,2})//(\d{4})`)
	reCircaFull           = regexp.MustCompile(`(?i)^(circa|cir\.?|ca\.?|approx\.?|c\.?)\s*(\d{4})(.*)$`)
	reDecadeYear          = regexp.MustCompile(`^(\d{4})(s)?(-\d{4})?$`)
	reMonthYearUnanchored = regexp.MustCompile(monthList + `\.?\s*(\d{4})`)
	reMonthYY             = regexp.MustCompile(monthList + `[.\-]\s*(\d{2})`)
	reSameMonthDayRange   = regexp.MustCompile(`(?i)^(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2})\s+(?:-\s+)?(\d{1,2})\s+(\d{4})`)

	// ensure_chronological_order
	reRangeParts = regexp.MustCompile(`^(\d{1,2})/(\d{1,2})/(\d{4}) - (\d{1,2})/(\d{1,2})/(\d{4})`)

	// convert_strange_named_ranges
	reStrangeRange = regexp.MustCompile(`\b([A-Za-z]+) (\d{1,2})( \d{4})? - ([A-Za-z]*)? ?(\d{1,2})( \d{4})?`)

	// DC mode
	reDCFullRange         = regexp.MustCompile(`^\d{2}/\d{2}/\d{4} - \d{2}/\d{2}/\d{4}`)
	reDCISODate           = regexp.MustCompile(`^\d{4}-\d{2}-\d{2}$`)
	reDCISOTimestamp      = regexp.MustCompile(`^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}$`)
	reDCYearDashYear      = regexp.MustCompile(`^\d{4}-\d{4}$`)
	reDCYYYYslashYYYYMM   = regexp.MustCompile(`^\d{4}/\d{4}-\d{2}$`)
	reDCYYYYMMslashYYYY   = regexp.MustCompile(`^\d{4}-\d{2}/\d{4}$`)
	reDCYYYYMMslashYYYYMM = regexp.MustCompile(`^\d{4}-\d{2}/\d{4}-\d{2}$`)
	reDCSlashYears        = regexp.MustCompile(`^\d{4}(/\d{4})+`)
	reDCISORange          = regexp.MustCompile(`^\d{4}-\d{2}-\d{2}/\d{4}-\d{2}-\d{2}$`)
	reDCMixedRange        = regexp.MustCompile(`^\d{2}-\d{2}-\d{4}/\d{4}-\d{2}-\d{2}$`)
	reDCToRange           = regexp.MustCompile(`(?i)^\d{4}-\d{2}-\d{2} (To|TO|to) \d{4}-\d{2}-\d{2}`)
	reDCYear              = regexp.MustCompile(`^\d{4}$`)
	reDCMonthYear         = regexp.MustCompile(monthList + `\.?\s*(\d{4})`)
	reDCZeroDay           = regexp.MustCompile(`^(\d{1,2})/0+/(\d{4})`)
	reDCYYYYMM            = regexp.MustCompile(`^\d{4}-\d{2}$`)
)

// ── Utility functions ─────────────────────────────────────────────────────────

// GetLastDayOfMonth returns the last calendar day of the given month/year.
func GetLastDayOfMonth(year, month int) int {
	return time.Date(year, time.Month(month+1), 0, 0, 0, 0, 0, time.UTC).Day()
}

// ExcelSerialToDate converts an Excel date serial to MM/DD/YYYY.
// Uses a dual base to handle Excel's 1900 leap-year bug: serials < 60 use
// 1899-12-31 as base; serials >= 60 use 1899-12-30.
func ExcelSerialToDate(serial int) string {
	base := time.Date(1899, 12, 31, 0, 0, 0, 0, time.UTC)
	if serial >= 60 {
		base = time.Date(1899, 12, 30, 0, 0, 0, 0, time.UTC)
	}
	d := base.AddDate(0, 0, serial)
	return fmt.Sprintf("%02d/%02d/%04d", d.Month(), d.Day(), d.Year())
}

// ExpandTwoDigitYear uses the project pivot for ambiguous numeric YY dates.
func ExpandTwoDigitYear(yy int) int {
	if yy <= 29 {
		return 2000 + yy
	}
	return 1900 + yy
}

// FormatTwoDigitYearDate converts M/D/YY or M-D-YY to MM/DD/YYYY.
func FormatTwoDigitYearDate(s string) (string, bool) {
	m := reYYDate.FindStringSubmatch(strings.TrimSpace(s))
	if m == nil || m[2] != m[4] {
		return "", false
	}
	mo, day, year := atoi(m[1]), atoi(m[3]), ExpandTwoDigitYear(atoi(m[5]))
	if !validDate(year, mo, day) {
		return "", false
	}
	return fmt.Sprintf("%02d/%02d/%04d", mo, day, year), true
}

// HasTwoDigitYearDate reports whether input contains an ambiguous M/D/YY date.
func HasTwoDigitYearDate(s string) bool {
	for _, m := range reYYDateScan.FindAllStringSubmatch(s, -1) {
		if m[3] == m[5] {
			return true
		}
	}
	return false
}

func validDate(year, month, day int) bool {
	if month < 1 || month > 12 || day < 1 {
		return false
	}
	return day <= GetLastDayOfMonth(year, month)
}

// PadAlnum pads a value to the given width. Pure-numeric values are
// zero-padded; values with a single leading letter have their digit portion
// padded; other shapes are returned unchanged.
func PadAlnum(val string, width int) string {
	val = strings.TrimSpace(val)
	if val == "" {
		return val
	}
	if isAllDigits(val) {
		if len(val) < width {
			return strings.Repeat("0", width-len(val)) + val
		}
		return val
	}
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

// IsPlausibleYearText returns true if s is a 4-digit year in 1000–2100.
func IsPlausibleYearText(s string) bool {
	if len(s) != 4 {
		return false
	}
	n, err := strconv.Atoi(s)
	if err != nil {
		return false
	}
	return n >= 1000 && n <= 2100
}

// IsExcelSerialText returns true if s looks like an Excel date serial
// (exactly 5 digits, not a plausible 4-digit year).
func IsExcelSerialText(s string) bool {
	if len(s) != 5 {
		return false
	}
	_, err := strconv.Atoi(s)
	return err == nil
}

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
	if strings.HasPrefix(v, "circa ") ||
		strings.HasPrefix(v, "before ") ||
		strings.HasPrefix(v, "after ") {
		return true
	}
	return false
}

func atoi(s string) int {
	n, _ := strconv.Atoi(strings.TrimSpace(s))
	return n
}

func addLeadingZeros(s string) string {
	s = reLeadZero1.ReplaceAllString(s, "0$1/$2/$3")
	s = reLeadZero2.ReplaceAllString(s, "$1/0$2/$3")
	return s
}

func excelSerial(s string) string {
	n, err := strconv.Atoi(strings.TrimSpace(s))
	if err != nil {
		return ""
	}
	return ExcelSerialToDate(n)
}

func normBeforeAfter(kw, dateStr string) string {
	kw = strings.ToLower(kw)
	outKw := "before"
	if kw == "after" || kw == "post" {
		outKw = "after"
	}
	if strings.Contains(dateStr, "/") {
		parts := strings.Split(dateStr, "/")
		if len(parts) == 3 {
			mo, d, y := atoi(parts[0]), atoi(parts[1]), parts[2]
			return fmt.Sprintf("%s %02d/%02d/%s", outKw, mo, d, y)
		}
	}
	// year-only
	if outKw == "before" {
		return fmt.Sprintf("before 01/01/%s", dateStr)
	}
	return fmt.Sprintf("after 12/31/%s", dateStr)
}

// circaResult handles the circa pattern without lookaheads.
// Returns ("circa YYYY", true) when year is NOT followed by -DD,
// returns ("", false) when it IS followed by ISO format (caller should skip).
func circaResult(s string) (string, bool, bool) {
	m := reCircaFull.FindStringSubmatch(s)
	if m == nil {
		return "", false, false
	}
	year, rest := m[2], strings.TrimSpace(m[3])
	// If rest starts with -NN, it's part of an ISO date → preserve as-is
	if len(rest) >= 3 && rest[0] == '-' && rest[1] >= '0' && rest[1] <= '9' && rest[2] >= '0' && rest[2] <= '9' {
		return "", false, true // signal: skip normalization, pass through
	}
	return "circa " + year, true, true
}

// ── AE pipeline (custom_format_date) ─────────────────────────────────────────

// CustomFormatDate converts input using the ArchivEra range pipeline.
// Returns (value, flagged).
func CustomFormatDate(s string) (string, bool) {
	defer func() { recover() }() // match Python's broad except

	if strings.TrimSpace(s) == "" {
		return "undated", false
	}

	// Strip parenthetical content
	s = strings.TrimSpace(reParens.ReplaceAllString(s, ""))
	s = addLeadingZeros(s)

	// 1. Already formatted range
	if reFullRange.MatchString(s) {
		return s, false
	}

	if v, ok := FormatTwoDigitYearDate(s); ok {
		return v, true
	}

	// 2. Plausible year
	if IsPlausibleYearText(s) {
		return fmt.Sprintf("01/01/%s - 12/31/%s", s, s), false
	}

	// 3. Excel serial
	if IsExcelSerialText(s) {
		return excelSerial(s), true
	}

	// 4. Multi-year (1998,1999 / 1998-1999-2000 etc.)
	if reMultiYear.MatchString(s) {
		found := regexp.MustCompile(`\d{4}`).FindAllString(s, -1)
		if len(found) > 1 {
			years := uniqueSortedYears(found)
			return fmt.Sprintf("01/01/%d - 12/31/%d", years[0], years[len(years)-1]), true
		}
	}

	// 5. Month Day, Year – Month Day, Year (em-dash or hyphen, various forms)
	if m := reMonthRangeA.FindStringSubmatch(s); m != nil {
		sn, ok1 := toMonthNum(m[1])
		en, ok2 := toMonthNum(m[4])
		if ok1 && ok2 {
			return fmt.Sprintf("%02d/%s/%s - %02d/%s/%s",
				sn, zeroPad(m[2]), m[3], en, zeroPad(m[5]), m[6]), false
		}
	}

	// 6. Month Day, Year - Month Day, Year (comma+space required)
	if m := reMonthRangeB.FindStringSubmatch(s); m != nil {
		sn, ok1 := toMonthNum(m[1])
		en, ok2 := toMonthNum(m[4])
		if ok1 && ok2 {
			return fmt.Sprintf("%02d/%s/%s - %02d/%s/%s",
				sn, zeroPad(m[2]), m[3], en, zeroPad(m[5]), m[6]), false
		}
	}

	// 7. Month YYYY (anchored)
	if m := reMonthYearAnchor.FindStringSubmatch(s); m != nil {
		mo, y := m[1], m[2]
		mn, ok := toMonthNum(mo)
		if ok {
			last := GetLastDayOfMonth(atoi(y), mn)
			return fmt.Sprintf("%02d/01/%s - %02d/%02d/%s", mn, y, mn, last, y), false
		}
	}

	// 8. Month Day Year / Month Dth, Year
	if m := reMonthDayYear.FindStringSubmatch(s); m != nil {
		mo, day, year := m[1], m[2], m[3]
		mn, ok := toMonthNum(mo)
		if ok {
			return fmt.Sprintf("%02d/%s/%s", mn, zeroPad(day), year), false
		}
	}

	// 9. YYYY Vol/Volume
	if m := reVolYear.FindStringSubmatch(s); m != nil {
		y := m[1]
		return fmt.Sprintf("01/01/%s - 12/31/%s", y, y), true
	}

	// 10. No-date markers
	if reNoDate.MatchString(s) {
		return "undated", false
	}

	// 11. Serial range: NNNNN - NNNNN
	if m := reSerialRange.FindStringSubmatch(s); m != nil {
		sd := ""
		if m[1] != "" {
			sd = excelSerial(m[1])
		}
		ed := ""
		if m[2] != "" {
			ed = excelSerial(m[2])
		}
		if sd != "" && ed != "" {
			return fmt.Sprintf("%s - %s", sd, ed), false
		}
		if sd != "" {
			return sd, true
		}
		if ed != "" {
			return ed, true
		}
	}

	// 12. ISO date: YYYY-MM-DD or YYYY/MM/DD
	if m := reISODateAE.FindStringSubmatch(s); m != nil {
		y, mo, d := atoi(m[1]), atoi(m[2]), atoi(m[3])
		return fmt.Sprintf("%02d/%02d/%04d", mo, d, y), false
	}

	// 13. before/pre/ante/after/post
	if m := rePrePost.FindStringSubmatch(s); m != nil {
		return normBeforeAfter(m[1], m[2]), true
	}

	// 14. ISO timestamp: YYYY-MM-DD HH:MM:SS
	if reISOTimestamp.MatchString(s) {
		t, err := time.Parse("2006-01-02", s[:10])
		if err == nil {
			return t.Format("01/02/2006"), false
		}
	}

	// 15. Year range: YYYY - YYYY
	if m := reYearRange.FindStringSubmatch(s); m != nil {
		return fmt.Sprintf("01/01/%s - 12/31/%s", m[1], m[2]), false
	}

	// 16. ISO month/year slash range: YYYY/MM - YYYY/MM
	if m := reISOMonthSlash.FindStringSubmatch(s); m != nil {
		sy, smo, ey, emo := atoi(m[1]), atoi(m[2]), atoi(m[3]), atoi(m[4])
		last := GetLastDayOfMonth(ey, emo)
		return fmt.Sprintf("%02d/01/%04d - %02d/%02d/%04d", smo, sy, emo, last, ey), false
	}

	// 17. Abbreviated year: YYYY-YY
	if m := reYYYYMM.FindStringSubmatch(s); m != nil {
		sy := m[1]
		suffix := atoi(m[2])
		lastTwo := atoi(sy[2:])
		ey := atoi(sy[:2] + m[2])
		if suffix < lastTwo {
			ey += 100
		}
		return fmt.Sprintf("01/01/%s - 12/31/%04d", sy, ey), false
	}

	// 18. ?? - MM/DD/YYYY
	if m := reQQBeforeDate.FindStringSubmatch(s); m != nil {
		mo, d, y := atoi(m[1]), atoi(m[2]), m[3]
		return fmt.Sprintf("before %02d/%02d/%s", mo, d, y), true
	}

	// 19. ?? - YYYY
	if m := reQQBeforeYear.FindStringSubmatch(s); m != nil {
		return fmt.Sprintf("before %s", m[1]), true
	}

	// 20. MM/DD/YYYY - ??
	if m := reAfterDate.FindStringSubmatch(s); m != nil {
		mo, d, y := atoi(m[1]), atoi(m[2]), m[3]
		return fmt.Sprintf("after %02d/%02d/%s", mo, d, y), true
	}

	// 21. Zero-day range: MM/0/YYYY - MM/0/YYYY
	if m := reZeroDayRange.FindStringSubmatch(s); m != nil {
		ms, ys, me, ye := atoi(m[1]), m[2], atoi(m[3]), m[4]
		last := GetLastDayOfMonth(atoi(ye), me)
		return fmt.Sprintf("%02d/01/%s - %02d/%02d/%s", ms, ys, me, last, ye), false
	}

	// 22. Zero-day single: MM/0/YYYY
	if m := reZeroDay.FindStringSubmatch(s); m != nil {
		mo, y := atoi(m[1]), m[2]
		last := GetLastDayOfMonth(atoi(y), mo)
		return fmt.Sprintf("%02d/01/%s - %02d/%02d/%s", mo, y, mo, last, y), false
	}

	// 23. Double-slash: MM//YYYY
	if m := reDoubleSlash.FindStringSubmatch(s); m != nil {
		mo, y := atoi(m[1]), m[2]
		last := GetLastDayOfMonth(atoi(y), mo)
		return fmt.Sprintf("%02d/01/%s - %02d/%02d/%s", mo, y, mo, last, y), false
	}

	// 24. " - " split (handles ranges and ?? / 00 day patterns)
	if strings.Contains(s, " - ") {
		sd, ed, ok := splitRange(s)
		if ok {
			if sdy, ok1 := FormatTwoDigitYearDate(sd); ok1 {
				if edy, ok2 := FormatTwoDigitYearDate(ed); ok2 {
					return fmt.Sprintf("%s - %s", sdy, edy), true
				}
			}
			if hasFuzzyDay(sd) || hasFuzzyDay(ed) {
				smo, sys, emo, eye, ok2 := extractMonthYear(sd, ed)
				if ok2 {
					last := GetLastDayOfMonth(atoi(eye), emo)
					return fmt.Sprintf("%02d/01/%s - %02d/%02d/%s", smo, sys, emo, last, eye), false
				}
				return s, false
			}
			sdf, err1 := time.Parse("01/02/2006", sd)
			edf, err2 := time.Parse("01/02/2006", ed)
			if err1 == nil && err2 == nil {
				return fmt.Sprintf("%s - %s", sdf.Format("01/02/2006"), edf.Format("01/02/2006")), false
			}
			return s, false
		}
	} else {
		t, err := time.Parse("01/02/2006", s)
		if err == nil {
			return t.Format("01/02/2006"), false
		}
	}

	// 25. circa (without ISO-date suffix)
	if v, flagged, matched := circaResult(s); matched {
		if v != "" {
			return v, flagged
		}
		// circa YYYY-MM-DD → fall through to pass-through
	}

	// 26. Decade / year fullmatch: 1960s, 1960-1975
	if m := reDecadeYear.FindStringSubmatch(s); m != nil {
		y, suffix, rangePart := m[1], m[2], m[3]
		if rangePart != "" {
			ey := rangePart[1:] // strip leading "-"
			return fmt.Sprintf("01/01/%s - 12/31/%s", y, ey), false
		} else if suffix == "s" {
			return fmt.Sprintf("01/01/%s - 12/31/%d", y, atoi(y)+9), false
		}
		// pure year already handled by IsPlausibleYearText above
		return fmt.Sprintf("01/01/%s - 12/31/%s", y, y), false
	}

	// 27. ?? within date string
	if strings.Contains(s, "??") {
		slashes := strings.Count(s, "/")
		if slashes == 2 {
			parts := strings.Split(s, "/")
			if len(parts) == 3 && parts[1] == "??" {
				mo, y := atoi(parts[0]), parts[2]
				last := GetLastDayOfMonth(atoi(y), mo)
				return fmt.Sprintf("%02d/01/%s - %02d/%02d/%s", mo, y, mo, last, y), false
			}
			return s, false
		} else if strings.HasPrefix(s, "??/") {
			parts := strings.Split(s, "/")
			if len(parts) >= 2 {
				y := parts[1]
				return fmt.Sprintf("01/01/%s - 12/31/%s", y, y), false
			}
		}
	}

	// 28. Month YYYY (unanchored fallback)
	if m := reMonthYearUnanchored.FindStringSubmatch(s); m != nil {
		mo, y := m[1], m[2]
		mn, ok := toMonthNum(mo)
		if ok {
			last := GetLastDayOfMonth(atoi(y), mn)
			return fmt.Sprintf("%02d/01/%s - %02d/%02d/%s", mn, y, mn, last, y), false
		}
	}

	// 29. Month-YY (Jun-62)
	if m := reMonthYY.FindStringSubmatch(s); m != nil {
		mo, y2 := m[1], atoi(m[2])
		mn, ok := toMonthNum(mo)
		if ok {
			y := 1900 + y2
			if y2 < 50 {
				y = 2000 + y2
			}
			last := GetLastDayOfMonth(y, mn)
			return fmt.Sprintf("%02d/01/%04d - %02d/%02d/%04d", mn, y, mn, last, y), false
		}
	}

	// 30. Same-month day range: January 1 - 31 1990
	if m := reSameMonthDayRange.FindStringSubmatch(s); m != nil {
		mname, sd, ed, y := m[1], m[2], m[3], m[4]
		mn, ok := toMonthNum(mname)
		if ok {
			return fmt.Sprintf("%02d/%s/%s - %02d/%s/%s",
				mn, zeroPad(sd), y, mn, zeroPad(ed), y), false
		}
	}

	return s, true
}

// ── Helpers for AE split block ────────────────────────────────────────────────

func splitRange(s string) (sd, ed string, ok bool) {
	idx := strings.Index(s, " - ")
	if idx < 0 {
		return
	}
	return s[:idx], s[idx+3:], true
}

func hasFuzzyDay(part string) bool {
	return strings.Contains(part, "??") || strings.Contains(part, "/00/") ||
		strings.Contains(part, "/0/") || strings.Contains(part, "//")
}

func extractMonthYear(sd, ed string) (smo int, sys string, emo int, eye string, ok bool) {
	sp := strings.Split(sd, "/")
	ep := strings.Split(ed, "/")
	if len(sp) != 3 || len(ep) != 3 {
		return
	}
	smo = atoi(sp[0])
	sys = sp[2]
	emo = atoi(ep[0])
	eye = ep[2]
	if smo == 0 || emo == 0 || sys == "" || eye == "" {
		return
	}
	ok = true
	return
}

func zeroPad(s string) string {
	s = strings.TrimSpace(s)
	n, err := strconv.Atoi(s)
	if err != nil {
		return s
	}
	return fmt.Sprintf("%02d", n)
}

func uniqueSortedYears(strs []string) []int {
	seen := map[int]bool{}
	for _, s := range strs {
		n, err := strconv.Atoi(s)
		if err == nil {
			seen[n] = true
		}
	}
	var years []int
	for y := range seen {
		years = append(years, y)
	}
	// simple sort
	for i := 0; i < len(years); i++ {
		for j := i + 1; j < len(years); j++ {
			if years[j] < years[i] {
				years[i], years[j] = years[j], years[i]
			}
		}
	}
	return years
}

// ── Strange named ranges ──────────────────────────────────────────────────────

// ConvertStrangeNamedRanges handles named month ranges like
// "Feb 1 2000 - Feb 29 2000", "Jan 1 - 31 1990", etc.
func ConvertStrangeNamedRanges(s string) string {
	m := reStrangeRange.FindStringSubmatch(s)
	if m == nil {
		return s
	}
	sm, sd := m[1], strings.TrimSpace(m[2])
	syOpt, emOpt, ed, eyOpt := strings.TrimSpace(m[3]), strings.TrimSpace(m[4]), strings.TrimSpace(m[5]), strings.TrimSpace(m[6])

	sy := syOpt
	if sy == "" {
		sy = eyOpt
	}
	em := emOpt
	if em == "" {
		em = sm
	}

	var startDate, endDate time.Time
	var err error
	for _, layout := range []string{"January 2 2006", "Jan 2 2006"} {
		startDate, err = time.Parse(layout, fmt.Sprintf("%s %s %s", sm, sd, sy))
		if err == nil {
			break
		}
	}
	if err != nil {
		return s
	}
	for _, layout := range []string{"January 2 2006", "Jan 2 2006"} {
		endDate, err = time.Parse(layout, fmt.Sprintf("%s %s %s", em, ed, eyOpt))
		if err == nil {
			break
		}
	}
	if err != nil {
		return s
	}
	return fmt.Sprintf("%s - %s", startDate.Format("01/02/2006"), endDate.Format("01/02/2006"))
}

// ── Chronological order ───────────────────────────────────────────────────────

// EnsureChronologicalOrder swaps start/end dates if they are reversed.
func EnsureChronologicalOrder(s string) string {
	m := reRangeParts.FindStringSubmatch(s)
	if m == nil {
		return s
	}
	sm, sd, sy := atoi(m[1]), atoi(m[2]), m[3]
	em, ed, ey := atoi(m[4]), atoi(m[5]), m[6]

	start, err1 := time.Parse("01/02/2006", fmt.Sprintf("%02d/%02d/%s", sm, sd, sy))
	end, err2 := time.Parse("01/02/2006", fmt.Sprintf("%02d/%02d/%s", em, ed, ey))
	if err1 != nil || err2 != nil {
		return s
	}
	if start.After(end) {
		start, end = end, start
	}
	return fmt.Sprintf("%s - %s", start.Format("01/02/2006"), end.Format("01/02/2006"))
}

// ── Dublin Core pipeline (convert_date_pattern) ───────────────────────────────

// ConvertDatePattern converts input using the Dublin Core pipeline.
func ConvertDatePattern(s string) string {
	defer func() { recover() }()

	if strings.TrimSpace(s) == "" {
		return "undated"
	}

	// 1. Already formatted range (pass through)
	if reDCFullRange.MatchString(s) {
		return s
	}

	// Strip parenthetical content
	s = strings.TrimSpace(reParens.ReplaceAllString(s, ""))

	if v, ok := FormatTwoDigitYearDate(s); ok {
		return v
	}
	if strings.Contains(s, " - ") {
		sd, ed, ok := splitRange(s)
		if ok {
			if sdy, ok1 := FormatTwoDigitYearDate(sd); ok1 {
				if edy, ok2 := FormatTwoDigitYearDate(ed); ok2 {
					return fmt.Sprintf("%s - %s", sdy, edy)
				}
			}
		}
	}

	// 2. Excel serial (5 digits)
	if IsExcelSerialText(s) {
		return excelSerial(s)
	}

	// 3. Serial range
	if m := reSerialRange.FindStringSubmatch(s); m != nil {
		sd := ""
		if m[1] != "" {
			sd = excelSerial(m[1])
		}
		ed := ""
		if m[2] != "" {
			ed = excelSerial(m[2])
		}
		if sd != "" && ed != "" {
			return fmt.Sprintf("%s - %s", sd, ed)
		}
		if sd != "" {
			return sd
		}
		if ed != "" {
			return ed
		}
	}

	// 4. No-date markers
	if reNoDate.MatchString(s) {
		return "undated"
	}

	// 5. ISO timestamp: YYYY-MM-DD HH:MM:SS
	if reDCISOTimestamp.MatchString(s) {
		t, err := time.Parse("2006-01-02", s[:10])
		if err == nil {
			return t.Format("01/02/2006")
		}
	}

	// 6. ISO date: YYYY-MM-DD
	if reDCISODate.MatchString(s) {
		t, err := time.Parse("2006-01-02", s)
		if err == nil {
			return t.Format("01/02/2006")
		}
	}

	// 7. Year-year: YYYY-YYYY
	if reDCYearDashYear.MatchString(s) {
		parts := strings.Split(s, "-")
		return fmt.Sprintf("01/01/%s - 12/31/%s", parts[0], parts[1])
	}

	// 8. YYYY/YYYY-MM
	if reDCYYYYslashYYYYMM.MatchString(s) {
		slash := strings.Index(s, "/")
		sy := s[:slash]
		rest := s[slash+1:]
		dash := strings.Index(rest, "-")
		ey, emo := rest[:dash], atoi(rest[dash+1:])
		last := GetLastDayOfMonth(atoi(ey), emo)
		return fmt.Sprintf("01/01/%s - %02d/%02d/%s", sy, emo, last, ey)
	}

	// 9. YYYY-MM/YYYY
	if reDCYYYYMMslashYYYY.MatchString(s) {
		slash := strings.Index(s, "/")
		sp := s[:slash]
		ey := s[slash+1:]
		dash := strings.Index(sp, "-")
		sy, smo := sp[:dash], atoi(sp[dash+1:])
		return fmt.Sprintf("%02d/01/%s - 12/31/%s", smo, sy, ey)
	}

	// 10. YYYY-MM/YYYY-MM
	if reDCYYYYMMslashYYYYMM.MatchString(s) {
		slash := strings.Index(s, "/")
		sp, ep := s[:slash], s[slash+1:]
		d1 := strings.Index(sp, "-")
		d2 := strings.Index(ep, "-")
		sy, smo := sp[:d1], atoi(sp[d1+1:])
		ey, emo := ep[:d2], atoi(ep[d2+1:])
		last := GetLastDayOfMonth(atoi(ey), emo)
		return fmt.Sprintf("%02d/01/%s - %02d/%02d/%s", smo, sy, emo, last, ey)
	}

	// 11. YYYY/YYYY(/YYYY)* slash-separated years
	if reDCSlashYears.MatchString(s) {
		years := strings.Split(s, "/")
		return fmt.Sprintf("01/01/%s - 12/31/%s", years[0], years[len(years)-1])
	}

	// 12. YYYY-MM-DD/YYYY-MM-DD ISO range
	if reDCISORange.MatchString(s) {
		slash := strings.Index(s, "/")
		sd, ed := s[:slash], s[slash+1:]
		ts, err1 := time.Parse("2006-01-02", sd)
		te, err2 := time.Parse("2006-01-02", ed)
		if err1 == nil && err2 == nil {
			return fmt.Sprintf("%s - %s", ts.Format("01/02/2006"), te.Format("01/02/2006"))
		}
	}

	// 13. YYYY-MM (ISO partial month OR abbreviated year range)
	if reDCYYYYMM.MatchString(s) {
		dash := strings.LastIndex(s, "-")
		yStr, suffStr := s[:dash], s[dash+1:]
		suffix := atoi(suffStr)
		if suffix > 12 {
			// abbreviated year range, e.g. 1898-01 → 1898–1901
			ey := atoi(yStr[:2] + suffStr)
			if suffix < atoi(yStr[2:]) {
				ey += 100
			}
			return fmt.Sprintf("01/01/%s - 12/31/%04d", yStr, ey)
		}
		// month: e.g. 1962-06
		y, mo := atoi(yStr), suffix
		last := GetLastDayOfMonth(y, mo)
		return fmt.Sprintf("%02d/01/%04d - %02d/%02d/%04d", mo, y, mo, last, y)
	}

	// 14. Standalone year: YYYY
	if reDCYear.MatchString(s) {
		return fmt.Sprintf("01/01/%s - 12/31/%s", s, s)
	}

	// 15. MM-DD-YYYY/YYYY-MM-DD mixed ISO range
	if reDCMixedRange.MatchString(s) {
		slash := strings.Index(s, "/")
		sd, ed := s[:slash], s[slash+1:]
		ts, err1 := time.Parse("01-02-2006", sd)
		te, err2 := time.Parse("2006-01-02", ed)
		if err1 == nil && err2 == nil {
			return fmt.Sprintf("%s - %s", ts.Format("01/02/2006"), te.Format("01/02/2006"))
		}
	}

	// 16. YYYY-MM-DD TO YYYY-MM-DD
	if reDCToRange.MatchString(s) {
		replaced := regexp.MustCompile(`(?i)\s+(To|TO|to)\s+`).ReplaceAllString(s, "/")
		return ConvertDatePattern(replaced)
	}

	// 17. before/pre/ante/after/post
	if m := rePrePost.FindStringSubmatch(s); m != nil {
		return normBeforeAfter(m[1], m[2])
	}

	// 18. circa (without ISO-date suffix)
	if v, _, matched := circaResult(s); matched {
		if v != "" {
			return v
		}
		// circa YYYY-MM-DD → pass through as-is
		return s
	}

	// 19. Month YYYY
	if m := reDCMonthYear.FindStringSubmatch(s); m != nil {
		mo, y := m[1], m[2]
		mn, ok := toMonthNum(mo)
		if ok {
			last := GetLastDayOfMonth(atoi(y), mn)
			return fmt.Sprintf("%02d/01/%s - %02d/%02d/%s", mn, y, mn, last, y)
		}
	}

	// 20. Zero-day: MM/0/YYYY
	if m := reDCZeroDay.FindStringSubmatch(s); m != nil {
		mo, y := atoi(m[1]), m[2]
		last := GetLastDayOfMonth(atoi(y), mo)
		return fmt.Sprintf("%02d/01/%s - %02d/%02d/%s", mo, y, mo, last, y)
	}

	return s
}

// ── Single-date pipeline ──────────────────────────────────────────────────────

// FormatSingleDate returns the first date (MM/DD/YYYY) from any input,
// or "" if the input cannot be resolved to a single date.
func FormatSingleDate(s string) string {
	if s == "" {
		return ""
	}
	lower := strings.ToLower(s)
	for _, nd := range []string{"undated", "n.d.", "nd", "n d", "no date"} {
		if lower == nd {
			return ""
		}
	}
	v, _ := CustomFormatDate(s)
	v = EnsureChronologicalOrder(v)
	if strings.Contains(v, " - ") {
		return strings.SplitN(v, " - ", 2)[0]
	}
	if regexp.MustCompile(`^\d{2}/\d{2}/\d{4}$`).MatchString(v) {
		return v
	}
	return ""
}
