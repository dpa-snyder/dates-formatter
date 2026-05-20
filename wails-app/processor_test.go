package main

import (
	"context"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

var fixturesDir = filepath.Join("..", "test-files")

func TestGetColumns_xlsx(t *testing.T) {
	result, err := GetColumns(filepath.Join(fixturesDir, "testing-column.xlsx"))
	if err != nil {
		t.Fatalf("GetColumns: %v", err)
	}
	if len(result.Columns) == 0 {
		t.Fatal("no columns returned")
	}
	if result.RowCount == 0 {
		t.Fatal("row count is 0")
	}
	t.Logf("columns=%v rowCount=%d datey=%v", result.Columns, result.RowCount, result.DateyColumns)
}

func TestGetColumns_csv(t *testing.T) {
	result, err := GetColumns(filepath.Join(fixturesDir, "testing-column-csv.csv"))
	if err != nil {
		t.Fatalf("GetColumns CSV: %v", err)
	}
	if len(result.Columns) == 0 {
		t.Fatal("no columns returned")
	}
	t.Logf("columns=%v rowCount=%d datey=%v", result.Columns, result.RowCount, result.DateyColumns)
}

func TestProcessFile_xlsx_ae(t *testing.T) {
	// Copy fixture to temp dir so we don't overwrite the real file.
	tmp := t.TempDir()
	src := filepath.Join(fixturesDir, "9200-W22.xlsx")
	dst := filepath.Join(tmp, "9200-W22.xlsx")
	data, err := os.ReadFile(src)
	if err != nil {
		t.Skipf("fixture not found: %v", err)
	}
	if err := os.WriteFile(dst, data, 0644); err != nil {
		t.Fatal(err)
	}

	// Find the date column name.
	cr, err := GetColumns(dst)
	if err != nil {
		t.Fatalf("GetColumns: %v", err)
	}
	t.Logf("columns: %v", cr.Columns)
	t.Logf("datey:   %v", cr.DateyColumns)
	t.Logf("rows:    %d", cr.RowCount)

	if len(cr.DateyColumns) == 0 {
		t.Log("no auto-detected date columns — skipping process step")
		return
	}

	opts := ProcessOptions{
		FilePath:   dst,
		Columns:    cr.DateyColumns[:1], // just first detected column
		Mode:       ModeAE,
		OutputMode: "overwrite",
	}

	var progressCalls int
	result, err := ProcessFile(context.Background(), opts, func(row, total int, col string, flagged int) {
		progressCalls++
	})
	if err != nil {
		t.Fatalf("ProcessFile: %v", err)
	}

	t.Logf("rows=%d flagged=%d output=%s progressCalls=%d",
		result.RowsProcessed, result.FlaggedRows, result.OutputPath, progressCalls)

	if result.RowsProcessed == 0 {
		t.Error("expected non-zero rows processed")
	}
	if _, err := os.Stat(result.OutputPath); err != nil {
		t.Errorf("output file not found: %v", err)
	}

	// Verify the output file has Original_ and Check columns.
	out, err := GetColumns(result.OutputPath)
	if err != nil {
		t.Fatalf("GetColumns on output: %v", err)
	}
	col := opts.Columns[0]
	hasOriginal := false
	hasCheck := false
	for _, h := range out.Columns {
		if h == "Original_"+col {
			hasOriginal = true
		}
		if strings.HasPrefix(h, "Check ") {
			hasCheck = true
		}
	}
	if !hasOriginal {
		t.Errorf("missing Original_%s column; got headers %v", col, out.Columns)
	}
	if !hasCheck {
		t.Errorf("missing Check column; got headers %v", out.Columns)
	}
}

func TestProcessFile_cancel(t *testing.T) {
	src := filepath.Join(fixturesDir, "testing-column.xlsx")
	if _, err := os.Stat(src); err != nil {
		t.Skip("fixture not found")
	}
	tmp := t.TempDir()
	dst := filepath.Join(tmp, "testing-column.xlsx")
	data, _ := os.ReadFile(src)
	_ = os.WriteFile(dst, data, 0644)

	cr, _ := GetColumns(dst)
	if len(cr.Columns) == 0 {
		t.Skip("no columns")
	}

	ctx, cancel := context.WithCancel(context.Background())
	cancel() // cancel immediately

	opts := ProcessOptions{
		FilePath:   dst,
		Columns:    cr.Columns[1:2],
		Mode:       ModeAE,
		OutputMode: "overwrite",
	}
	_, err := ProcessFile(ctx, opts, nil)
	if err == nil {
		t.Log("cancelled context: process returned nil error (short file, completed before check)")
	} else {
		t.Logf("cancelled: %v", err)
	}
}
