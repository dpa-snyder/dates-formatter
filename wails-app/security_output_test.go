package main

import (
	"bytes"
	"context"
	"errors"
	"io"
	"os"
	"path/filepath"
	"runtime"
	"testing"

	"github.com/xuri/excelize/v2"
)

func TestOutputPreservesExistingPermissionsAndNewOutputsArePrivate(t *testing.T) {
	if runtime.GOOS == "windows" {
		t.Skip("POSIX permission bits; Windows ACLs require platform verification")
	}
	for _, extension := range []string{".csv", ".xlsx"} {
		for _, mode := range []os.FileMode{0600, 0640} {
			path := filepath.Join(t.TempDir(), "output"+extension)
			if err := os.WriteFile(path, []byte("original bytes"), mode); err != nil {
				t.Fatal(err)
			}
			if err := os.Chmod(path, mode); err != nil {
				t.Fatal(err)
			}
			if err := writeOutput(context.Background(), path, []string{"Date"}, [][]string{{"1962"}}); err != nil {
				t.Fatal(err)
			}
			info, err := os.Stat(path)
			if err != nil {
				t.Fatal(err)
			}
			if info.Mode().Perm() != mode {
				t.Fatalf("%s mode = %o, want %o", extension, info.Mode().Perm(), mode)
			}
			if err := os.Remove(path); err != nil {
				t.Fatal(err)
			}
			if err := writeOutput(context.Background(), path, []string{"Date"}, [][]string{{"1962"}}); err != nil {
				t.Fatal(err)
			}
			info, err = os.Stat(path)
			if err != nil {
				t.Fatal(err)
			}
			if info.Mode().Perm() != 0600 {
				t.Fatalf("new %s mode = %o, want 600", extension, info.Mode().Perm())
			}
		}
	}
}

func TestOutputRejectsSymlinkAndDirectoryDestinations(t *testing.T) {
	for _, extension := range []string{".csv", ".xlsx"} {
		directory := t.TempDir()
		sentinel := filepath.Join(directory, "sentinel")
		if err := os.WriteFile(sentinel, []byte("unchanged sentinel"), 0600); err != nil {
			t.Fatal(err)
		}
		output := filepath.Join(directory, "output"+extension)
		if err := os.Symlink(sentinel, output); err != nil {
			if runtime.GOOS == "windows" {
				t.Skipf("symlink privileges unavailable: %v", err)
			}
			t.Fatal(err)
		}
		if err := writeOutput(context.Background(), output, []string{"Date"}, [][]string{{"1962"}}); err == nil {
			t.Fatal("symlink output accepted")
		}
		got, err := os.ReadFile(sentinel)
		if err != nil || string(got) != "unchanged sentinel" {
			t.Fatalf("sentinel changed: %v", err)
		}
		if err := os.Remove(output); err != nil {
			t.Fatal(err)
		}
		if err := os.Mkdir(output, 0700); err != nil {
			t.Fatal(err)
		}
		if err := writeOutput(context.Background(), output, []string{"Date"}, [][]string{{"1962"}}); err == nil {
			t.Fatal("directory output accepted")
		}
	}
}

func TestTemporaryOutputDescriptorDoesNotFollowSubstitutedName(t *testing.T) {
	directory := t.TempDir()
	sentinel := filepath.Join(directory, "sentinel")
	if err := os.WriteFile(sentinel, []byte("unchanged sentinel"), 0600); err != nil {
		t.Fatal(err)
	}
	location, err := openOutputDirectory(filepath.Join(directory, "output.csv"))
	if err != nil {
		t.Fatal(err)
	}
	defer location.close()
	staged, err := createOutputTemp(location, "output.csv")
	if err != nil {
		t.Fatal(err)
	}
	defer staged.close()
	output := staged.file
	if err := os.Remove(output.Name()); err != nil {
		if runtime.GOOS == "windows" {
			t.Skipf("platform prevents unlinking an open file: %v", err)
		}
		t.Fatal(err)
	}
	if err := os.Symlink(sentinel, output.Name()); err != nil {
		t.Fatal(err)
	}
	if err := writeCSV(output, []string{"Date"}, [][]string{{"1962"}}); err != nil {
		t.Fatal(err)
	}
	got, err := os.ReadFile(sentinel)
	if err != nil || string(got) != "unchanged sentinel" {
		t.Fatalf("substitution redirected writes: %v", err)
	}
	if _, err := output.Seek(0, io.SeekStart); err != nil {
		t.Fatal(err)
	}
	got, err = io.ReadAll(output)
	if err != nil || string(got) != "Date\n1962\n" {
		t.Fatalf("retained descriptor did not receive output: %v", err)
	}
}

type completedWriteContext struct {
	context.Context
	checks int
	hook   func()
}

func (c *completedWriteContext) Err() error {
	c.checks++
	if c.checks == 2 {
		c.hook()
	}
	return c.Context.Err()
}

func TestPrivateDirectorySubstitutionCannotChangePublishedBytes(t *testing.T) {
	if runtime.GOOS == "windows" {
		t.Skip("POSIX directory-entry substitution")
	}
	directory := t.TempDir()
	output := filepath.Join(directory, "output.csv")
	moved := filepath.Join(directory, "moved-private")
	var replacement string
	ctx := &completedWriteContext{Context: context.Background()}
	ctx.hook = func() {
		matches, err := filepath.Glob(filepath.Join(directory, ".date-formatter-*"))
		if err != nil || len(matches) != 1 {
			t.Fatalf("expected one private output directory: %v", err)
		}
		replacement = matches[0]
		if err := os.Rename(replacement, moved); err != nil {
			t.Fatal(err)
		}
		if err := os.Mkdir(replacement, 0700); err != nil {
			t.Fatal(err)
		}
		if err := os.WriteFile(filepath.Join(replacement, "output"), []byte("attacker bytes"), 0600); err != nil {
			t.Fatal(err)
		}
	}
	if err := writeOutput(ctx, output, []string{"Date"}, [][]string{{"1962"}}); err != nil {
		t.Fatal(err)
	}
	got, err := os.ReadFile(output)
	if err != nil || string(got) != "Date\n1962\n" {
		t.Fatalf("published replacement: %q %v", got, err)
	}
	got, err = os.ReadFile(filepath.Join(replacement, "output"))
	if err != nil || string(got) != "attacker bytes" {
		t.Fatalf("cleanup touched substitute: %q %v", got, err)
	}
}

func TestLateDirectoryDestinationIsNotMovedToBackup(t *testing.T) {
	directory := t.TempDir()
	output := filepath.Join(directory, "output.csv")
	if err := os.WriteFile(output, []byte("original"), 0600); err != nil {
		t.Fatal(err)
	}
	ctx := &completedWriteContext{Context: context.Background()}
	ctx.hook = func() {
		if err := os.Remove(output); err != nil {
			t.Fatal(err)
		}
		if err := os.Mkdir(output, 0700); err != nil {
			t.Fatal(err)
		}
		if err := os.WriteFile(filepath.Join(output, "sentinel"), []byte("unchanged"), 0600); err != nil {
			t.Fatal(err)
		}
	}
	if err := writeOutput(ctx, output, []string{"Date"}, [][]string{{"1962"}}); err == nil {
		t.Fatal("directory accepted")
	}
	got, err := os.ReadFile(filepath.Join(output, "sentinel"))
	if err != nil || string(got) != "unchanged" {
		t.Fatalf("directory moved or changed: %v", err)
	}
	matches, _ := filepath.Glob(output + ".date-formatter-backup-*")
	if len(matches) != 0 {
		t.Fatal("directory was moved to a backup")
	}
}

func TestOpenedOutputDirectoryCannotBeRedirectedDuringSave(t *testing.T) {
	if runtime.GOOS == "windows" {
		t.Skip("POSIX directory-entry substitution")
	}
	directory := t.TempDir()
	selected, victim := filepath.Join(directory, "selected"), filepath.Join(directory, "victim")
	for _, path := range []string{selected, victim} {
		if err := os.Mkdir(path, 0700); err != nil {
			t.Fatal(err)
		}
	}
	output := filepath.Join(selected, "output.csv")
	victimOutput := filepath.Join(victim, "output.csv")
	if err := os.WriteFile(victimOutput, []byte("private sentinel"), 0600); err != nil {
		t.Fatal(err)
	}
	location, err := openOutputDirectory(output)
	if err != nil {
		t.Fatal(err)
	}
	defer location.close()
	original := filepath.Join(directory, "original")
	if err := os.Rename(selected, original); err != nil {
		t.Fatal(err)
	}
	if err := os.Symlink(victim, selected); err != nil {
		t.Fatal(err)
	}
	if err := writeOutputInDirectory(context.Background(), output, []string{"Date"}, [][]string{{"1962"}}, location); err != nil {
		t.Fatal(err)
	}
	got, err := os.ReadFile(victimOutput)
	if err != nil || string(got) != "private sentinel" {
		t.Fatalf("ancestor swap redirected output: %v", err)
	}
	got, err = os.ReadFile(filepath.Join(original, "output.csv"))
	if err != nil || string(got) != "Date\n1962\n" {
		t.Fatalf("opened directory did not receive output: %v", err)
	}
}

type failedOutputWriter struct{}

func (failedOutputWriter) Write([]byte) (int, error) {
	return 0, io.ErrClosedPipe
}

func TestOutputWritersPropagateSerializationFailure(t *testing.T) {
	for name, writer := range map[string]func(io.Writer, []string, [][]string) error{
		"CSV": writeCSV, "XLSX": writeXLSX,
	} {
		t.Run(name, func(t *testing.T) {
			if err := writer(failedOutputWriter{}, []string{"Date"}, [][]string{{"1962"}}); !errors.Is(err, io.ErrClosedPipe) {
				t.Fatalf("write error = %v, want io.ErrClosedPipe", err)
			}
		})
	}
}

func TestXLSXDescriptorExportKeepsLiteralText(t *testing.T) {
	var output bytes.Buffer
	if err := writeXLSX(&output, []string{"=1+1"}, [][]string{{"=2+2"}, {"001.001"}}); err != nil {
		t.Fatal(err)
	}
	workbook, err := excelize.OpenReader(&output)
	if err != nil {
		t.Fatal(err)
	}
	defer workbook.Close()
	for cell, want := range map[string]string{"A1": "=1+1", "A2": "=2+2", "A3": "001.001"} {
		got, err := workbook.GetCellValue("Sheet1", cell)
		if err != nil || got != want {
			t.Fatalf("%s changed: %v", cell, err)
		}
		formula, err := workbook.GetCellFormula("Sheet1", cell)
		if err != nil || formula != "" {
			t.Fatalf("%s became a formula: %v", cell, err)
		}
	}
}

func TestWindowsStagedHandleIsExclusiveAndDirectoryBound(t *testing.T) {
	if runtime.GOOS != "windows" {
		t.Skip("native Windows handle publication")
	}
	parent := t.TempDir()
	selected := filepath.Join(parent, "selected")
	if err := os.Mkdir(selected, 0700); err != nil {
		t.Fatal(err)
	}
	location, err := openOutputDirectory(filepath.Join(selected, "output.csv"))
	if err != nil {
		t.Fatal(err)
	}
	defer location.close()
	staged, err := createOutputTemp(location, "output.csv")
	if err != nil {
		t.Fatal(err)
	}
	defer staged.close()
	if _, err := staged.file.WriteString("Date\n1962\n"); err != nil {
		t.Fatal(err)
	}
	if err := os.Remove(filepath.Join(selected, staged.directoryName, "output")); err == nil {
		t.Fatal("exclusive staged entry was removed")
	}
	moved := filepath.Join(parent, "original")
	swapped := false
	if err := os.Rename(selected, moved); err == nil {
		swapped = true
		if err := os.Mkdir(selected, 0700); err != nil {
			t.Fatal(err)
		}
		if err := os.WriteFile(filepath.Join(selected, "output.csv"), []byte("private sentinel"), 0600); err != nil {
			t.Fatal(err)
		}
	}
	if err := publishStagedOutput(staged, "output.csv"); err != nil {
		t.Fatal(err)
	}
	staged.published = true
	// Release the exclusive file handle before reading the published control.
	if err := staged.file.Close(); err != nil {
		t.Fatal(err)
	}
	actual := selected
	if swapped {
		actual = moved
		got, err := os.ReadFile(filepath.Join(selected, "output.csv"))
		if err != nil || string(got) != "private sentinel" {
			t.Fatalf("ancestor redirected output: %v", err)
		}
	}
	got, err := os.ReadFile(filepath.Join(actual, "output.csv"))
	if err != nil || string(got) != "Date\n1962\n" {
		t.Fatalf("opened directory did not receive control: %v", err)
	}
}
