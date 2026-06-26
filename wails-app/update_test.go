package main

import (
	"errors"
	"os"
	"testing"
)

func TestIsNewerVersion(t *testing.T) {
	cases := []struct {
		current string
		remote  string
		want    bool
	}{
		{"v0.2.12", "0.2.13", true},
		{"0.2.12", "v0.2.13", true},
		{"v0.2.12", "v0.2.12", false},
		{"v0.2.12", "v0.2.11", false},
		{"dev", "v0.2.13", false},
		{"v0.2.12", "", false},
	}
	for _, c := range cases {
		t.Run(c.current+"_"+c.remote, func(t *testing.T) {
			if got := isNewerVersion(c.current, c.remote); got != c.want {
				t.Fatalf("isNewerVersion(%q, %q) = %v, want %v", c.current, c.remote, got, c.want)
			}
		})
	}
}

func TestUpdateExecutablePath(t *testing.T) {
	cases := []struct {
		folder string
		want   string
	}{
		{`\\fileserver\apps\date-formatter`, `\\fileserver\apps\date-formatter\date-formatter.exe`},
		{`Z:\Apps\Date Formatter\`, `Z:\Apps\Date Formatter\date-formatter.exe`},
		{`X:\Apps\date-formatter.exe`, `X:\Apps\date-formatter.exe`},
		{`Z:\`, `Z:\date-formatter.exe`},
		{`/tmp/releases`, `/tmp/releases/date-formatter.exe`},
	}
	for _, c := range cases {
		t.Run(c.folder, func(t *testing.T) {
			if got := updateExecutablePath(c.folder); got != c.want {
				t.Fatalf("updateExecutablePath(%q) = %q, want %q", c.folder, got, c.want)
			}
		})
	}
}

func TestCheckUpdateCandidateUsesExeMetadata(t *testing.T) {
	readVersion := func(path string) (string, error) {
		if path != `\\fileserver\apps\date-formatter\date-formatter.exe` {
			t.Fatalf("read path = %q", path)
		}
		return "0.2.13", nil
	}

	result, err := checkUpdateCandidate("v0.2.12", `\\fileserver\apps\date-formatter`, readVersion)
	if err != nil {
		t.Fatalf("checkUpdateCandidate: %v", err)
	}
	if !result.UpdateAvailable {
		t.Fatal("expected update available")
	}
	if result.AvailableVersion != "0.2.13" {
		t.Fatalf("AvailableVersion = %q", result.AvailableVersion)
	}
	if result.SourcePath != `\\fileserver\apps\date-formatter\date-formatter.exe` {
		t.Fatalf("SourcePath = %q", result.SourcePath)
	}
}

func TestCheckUpdateCandidateNoopsWhenNoFolderOrNoNewerVersion(t *testing.T) {
	result, err := checkUpdateCandidate("v0.2.12", "", func(string) (string, error) {
		t.Fatal("readVersion should not be called")
		return "", nil
	})
	if err != nil {
		t.Fatalf("blank folder check: %v", err)
	}
	if result.UpdateAvailable {
		t.Fatal("blank folder should not report update")
	}

	result, err = checkUpdateCandidate("v0.2.12", `\\fileserver\apps`, func(string) (string, error) {
		return "0.2.12", nil
	})
	if err != nil {
		t.Fatalf("same version check: %v", err)
	}
	if result.UpdateAvailable {
		t.Fatal("same version should not report update")
	}
}

func TestCheckUpdateCandidateReturnsMetadataErrors(t *testing.T) {
	wantErr := errors.New("metadata unavailable")
	_, err := checkUpdateCandidate("v0.2.12", `\\fileserver\apps`, func(string) (string, error) {
		return "", wantErr
	})
	if !errors.Is(err, wantErr) {
		t.Fatalf("err = %v, want %v", err, wantErr)
	}
}

func TestStageUpdateExecutableCopiesExeToLocalCache(t *testing.T) {
	src, err := os.CreateTemp(t.TempDir(), "date-formatter-*.exe")
	if err != nil {
		t.Fatal(err)
	}
	if _, err := src.WriteString("new exe bytes"); err != nil {
		t.Fatal(err)
	}
	if err := src.Close(); err != nil {
		t.Fatal(err)
	}

	stagedPath, err := stageUpdateExecutable(src.Name())
	if err != nil {
		t.Fatalf("stageUpdateExecutable: %v", err)
	}
	t.Cleanup(func() { _ = os.Remove(stagedPath) })

	if stagedPath == src.Name() {
		t.Fatal("staged path should differ from source path")
	}
	got, err := os.ReadFile(stagedPath)
	if err != nil {
		t.Fatal(err)
	}
	if string(got) != "new exe bytes" {
		t.Fatalf("staged content = %q", string(got))
	}
}
