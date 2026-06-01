package main

import (
	"context"
	"encoding/csv"
	"fmt"
	"os"
	"path/filepath"
	"regexp"
	"strings"

	"date-formatter/dateengine"

	"github.com/xuri/excelize/v2"
)

// ── Regexps ───────────────────────────────────────────────────────────────────

var (
	reValidSingle = regexp.MustCompile(`^\d{2}/\d{2}/\d{4}$`)
	reValidRange  = regexp.MustCompile(`^\d{2}/\d{2}/\d{4} - \d{2}/\d{2}/\d{4}$`)
	reDateLike    = regexp.MustCompile(
		`^\d{1,2}/\d{1,2}/\d{4}` +
			`|^\d{4}-\d{2}-\d{2}` +
			`|^\d{4}$` +
			`|^\d{5}$` +
			`|(?i)^(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)` +
			`|\d{1,2}/\d{1,2}/\d{4} - \d{1,2}/\d{1,2}/\d{4}`)
)

// leadingZerosCols maps (lowercased) column header → pad width.
var leadingZerosCols = map[string]int{
	"rg":                  4,
	"record group number": 4,
	"sg":                  3,
	"subgr":               3,
	"subgroup":            3,
	"subgroup number":     3,
	"series":              3,
	"series number":       3,
	"subseries number":    3,
}

// ── Public types ──────────────────────────────────────────────────────────────

// ProgressFunc is called during processing to report progress.
type ProgressFunc func(row, total int, column string, flagged int)

// ── GetColumns ────────────────────────────────────────────────────────────────

// GetColumns reads the file at path and returns column names, row count, and
// columns that look like they contain dates (T-013 auto-detection).
func GetColumns(path string) (ColumnsResult, error) {
	var headers []string
	var rowCount int

	if isCSV(path) {
		h, rc, err := csvHeadersAndCount(path)
		if err != nil {
			return ColumnsResult{}, err
		}
		headers, rowCount = h, rc
	} else {
		h, rc, err := xlsxHeadersAndCount(path)
		if err != nil {
			return ColumnsResult{}, err
		}
		headers, rowCount = h, rc
	}

	datey := detectDateColumns(path, headers)
	return ColumnsResult{
		Columns:      headers,
		RowCount:     rowCount,
		DateyColumns: datey,
	}, nil
}

func csvHeadersAndCount(path string) ([]string, int, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, 0, err
	}
	defer f.Close()
	r := csv.NewReader(f)
	records, err := r.ReadAll()
	if err != nil {
		return nil, 0, err
	}
	if len(records) == 0 {
		return nil, 0, fmt.Errorf("empty CSV file")
	}
	return records[0], len(records) - 1, nil
}

func xlsxHeadersAndCount(path string) ([]string, int, error) {
	f, err := excelize.OpenFile(path)
	if err != nil {
		return nil, 0, err
	}
	defer f.Close()
	sheet := f.GetSheetName(0)
	rows, err := f.GetRows(sheet)
	if err != nil {
		return nil, 0, err
	}
	if len(rows) == 0 {
		return nil, 0, fmt.Errorf("empty xlsx file")
	}
	return rows[0], len(rows) - 1, nil
}

// detectDateColumns samples up to 20 non-empty cells per column and returns
// those where >50% match a date-like pattern (T-013).
func detectDateColumns(path string, headers []string) []string {
	var table [][]string

	if isCSV(path) {
		f, err := os.Open(path)
		if err != nil {
			return nil
		}
		defer f.Close()
		records, err := csv.NewReader(f).ReadAll()
		if err != nil || len(records) < 2 {
			return nil
		}
		table = records[1:]
	} else {
		f, err := excelize.OpenFile(path)
		if err != nil {
			return nil
		}
		defer f.Close()
		rows, err := f.GetRows(f.GetSheetName(0))
		if err != nil || len(rows) < 2 {
			return nil
		}
		table = rows[1:]
	}

	var datey []string
	for colIdx, header := range headers {
		matched, sampled := 0, 0
		for _, row := range table {
			if sampled >= 20 {
				break
			}
			val := ""
			if colIdx < len(row) {
				val = strings.TrimSpace(row[colIdx])
			}
			if val == "" {
				continue
			}
			sampled++
			if reDateLike.MatchString(val) {
				matched++
			}
		}
		if sampled >= 3 && matched*2 >= sampled {
			datey = append(datey, header)
		}
	}
	return datey
}

// ── ProcessFile ───────────────────────────────────────────────────────────────

// ProcessFile reads the file, converts selected columns, writes output.
func ProcessFile(ctx context.Context, opts ProcessOptions, progress ProgressFunc) (ProcessResult, error) {
	// Read table
	headers, rows, err := readTable(opts.FilePath)
	if err != nil {
		return ProcessResult{}, fmt.Errorf("read file: %w", err)
	}

	numRows := len(rows)
	numCols := len(opts.Columns)
	totalWork := numRows * numCols
	if totalWork == 0 {
		return ProcessResult{}, fmt.Errorf("no rows or columns to process")
	}

	deMode := toEngineMode(opts.Mode)
	engineOpts := dateengine.ConvertOptions{}
	if opts.YYOverrideEnabled {
		engineOpts.YYPrefix = dateengine.NormalizeYYPrefix(opts.YYPrefix)
		if engineOpts.YYPrefix == "" {
			return ProcessResult{}, fmt.Errorf("YY prefix must be exactly two digits")
		}
	}
	tick := numRows / 100
	if tick < 1 {
		tick = 1
	}

	results := make(map[string]*colResult, numCols)

	totalFlagged := 0
	workDone := 0

	for _, colName := range opts.Columns {
		select {
		case <-ctx.Done():
			return ProcessResult{}, ctx.Err()
		default:
		}

		colIdx := findColIdx(headers, colName)
		if colIdx < 0 {
			continue
		}

		cr := &colResult{
			converted: make([]string, numRows),
			flagged:   make([]bool, numRows),
		}

		for i, row := range rows {
			select {
			case <-ctx.Done():
				return ProcessResult{}, ctx.Err()
			default:
			}

			raw := ""
			if colIdx < len(row) {
				raw = row[colIdx]
			}

			res := dateengine.ConvertWithOptions(raw, deMode, engineOpts)
			cr.converted[i] = res.Value

			// Determine flagged state
			flagged := res.Flagged
			if !flagged {
				flagged = !isValidOutput(res.Value, deMode)
			}
			// AE extra: original contains semicolons → flag
			if deMode == dateengine.ModeAE && strings.Contains(raw, ";") {
				flagged = true
			}
			cr.flagged[i] = flagged
			if flagged {
				totalFlagged++
			}

			workDone++
			if i%tick == 0 && progress != nil {
				progress(workDone, totalWork, colName, totalFlagged)
			}
		}

		results[colName] = cr
	}

	// Build output headers
	newHeaders := buildHeaders(headers, opts.Columns)

	// Build output rows
	newRows := make([][]string, numRows)
	for i, row := range rows {
		newRows[i] = buildRow(row, headers, opts.Columns, results, i)
	}

	// Apply leading-zero padding to ID columns
	applyLeadingZeros(newHeaders, newRows)

	// Determine output path
	outPath := outputPath(opts.FilePath, opts.OutputMode)

	// Write
	if isCSV(outPath) {
		err = writeCSV(outPath, newHeaders, newRows)
	} else {
		err = writeXLSX(outPath, newHeaders, newRows)
	}
	if err != nil {
		return ProcessResult{}, fmt.Errorf("write output: %w", err)
	}

	return ProcessResult{
		RowsProcessed: numRows,
		FlaggedRows:   totalFlagged,
		OutputPath:    outPath,
		Columns:       opts.Columns,
	}, nil
}

// ── Table construction helpers ─────────────────────────────────────────────────

func buildHeaders(orig []string, selected []string) []string {
	sel := toSet(selected)
	out := make([]string, 0, len(orig)+len(selected)*2)
	for _, h := range orig {
		out = append(out, h)
		if sel[h] {
			out = append(out, "Original_"+h, "Check "+h)
		}
	}
	return out
}

func buildRow(
	row []string,
	origHeaders []string,
	selected []string,
	results map[string]*colResult,
	rowIdx int,
) []string {
	sel := toSet(selected)
	out := make([]string, 0, len(origHeaders)+len(selected)*2)
	for j, h := range origHeaders {
		raw := ""
		if j < len(row) {
			raw = row[j]
		}
		if cr, ok := results[h]; ok && sel[h] {
			check := ""
			if cr.flagged[rowIdx] {
				check = "Yes"
			}
			out = append(out, cr.converted[rowIdx], raw, check)
		} else {
			out = append(out, raw)
		}
	}
	return out
}

func applyLeadingZeros(headers []string, rows [][]string) {
	for j, h := range headers {
		width, ok := leadingZerosCols[strings.ToLower(strings.TrimSpace(h))]
		if !ok {
			continue
		}
		for i := range rows {
			if j < len(rows[i]) {
				rows[i][j] = dateengine.PadAlnum(rows[i][j], width)
			}
		}
	}
}

// ── File I/O ──────────────────────────────────────────────────────────────────

func readTable(path string) (headers []string, rows [][]string, err error) {
	if isCSV(path) {
		return readCSV(path)
	}
	return readXLSX(path)
}

func readCSV(path string) ([]string, [][]string, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, nil, err
	}
	defer f.Close()
	records, err := csv.NewReader(f).ReadAll()
	if err != nil {
		return nil, nil, err
	}
	if len(records) == 0 {
		return nil, nil, fmt.Errorf("empty CSV")
	}
	return records[0], records[1:], nil
}

func readXLSX(path string) ([]string, [][]string, error) {
	f, err := excelize.OpenFile(path)
	if err != nil {
		return nil, nil, err
	}
	defer f.Close()
	sheet := f.GetSheetName(0)
	rowData, err := f.GetRows(sheet)
	if err != nil {
		return nil, nil, err
	}
	if len(rowData) == 0 {
		return nil, nil, fmt.Errorf("empty xlsx")
	}
	// Normalize row widths to match header length
	hlen := len(rowData[0])
	data := make([][]string, len(rowData)-1)
	for i, row := range rowData[1:] {
		padded := make([]string, hlen)
		copy(padded, row)
		data[i] = padded
	}
	return rowData[0], data, nil
}

func writeCSV(path string, headers []string, rows [][]string) error {
	f, err := os.Create(path)
	if err != nil {
		return err
	}
	defer f.Close()
	w := csv.NewWriter(f)
	if err := w.Write(headers); err != nil {
		return err
	}
	for _, row := range rows {
		if err := w.Write(row); err != nil {
			return err
		}
	}
	w.Flush()
	return w.Error()
}

func writeXLSX(path string, headers []string, rows [][]string) error {
	f := excelize.NewFile()
	sheet := "Sheet1"
	f.SetSheetName(f.GetSheetName(0), sheet)

	// Create a text-format style (number_format = '@') to prevent Excel
	// from auto-converting leading-zero values like '001.001' → 1.001.
	textStyle, err := f.NewStyle(&excelize.Style{NumFmt: 49})
	if err != nil {
		textStyle = 0
	}

	// Write headers row 1
	for j, h := range headers {
		cell, _ := excelize.CoordinatesToCellName(j+1, 1)
		_ = f.SetCellStr(sheet, cell, h)
	}

	// Apply text format to entire columns
	for j := range headers {
		colName, _ := excelize.ColumnNumberToName(j + 1)
		_ = f.SetColStyle(sheet, colName, textStyle)
	}

	// Write data rows
	for i, row := range rows {
		for j, val := range row {
			cell, _ := excelize.CoordinatesToCellName(j+1, i+2)
			_ = f.SetCellStr(sheet, cell, val)
		}
	}

	return f.SaveAs(path)
}

// ── Utilities ─────────────────────────────────────────────────────────────────

func isCSV(path string) bool {
	return strings.EqualFold(filepath.Ext(path), ".csv")
}

func isValidOutput(v string, mode dateengine.Mode) bool {
	if v == "undated" {
		return true
	}
	switch mode {
	case dateengine.ModeSingle:
		return reValidSingle.MatchString(v)
	case dateengine.ModeAE, dateengine.ModeDC:
		return reValidSingle.MatchString(v) || reValidRange.MatchString(v)
	}
	return false
}

func toEngineMode(m Mode) dateengine.Mode {
	switch m {
	case ModeSingle:
		return dateengine.ModeSingle
	case ModeAE:
		return dateengine.ModeAE
	case ModeDC:
		return dateengine.ModeDC
	}
	return dateengine.ModeAE
}

func findColIdx(headers []string, name string) int {
	for i, h := range headers {
		if h == name {
			return i
		}
	}
	return -1
}

func toSet(ss []string) map[string]bool {
	m := make(map[string]bool, len(ss))
	for _, s := range ss {
		m[s] = true
	}
	return m
}

func outputPath(input, mode string) string {
	if mode == "overwrite" {
		return input
	}
	ext := filepath.Ext(input)
	stem := strings.TrimSuffix(input, ext)
	return stem + "-formatted" + ext
}

type colResult struct {
	converted []string
	flagged   []bool
}
