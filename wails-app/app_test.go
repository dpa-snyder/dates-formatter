package main

import "testing"

func TestOpenPathCommandWindowsUNC(t *testing.T) {
	cmd, args, err := openPathCommand("windows", `//DOSFS01/users/lindsay.townsend/Documents/9015-038-003-formatted.xlsx`)
	if err != nil {
		t.Fatalf("openPathCommand: %v", err)
	}
	if cmd != "explorer.exe" {
		t.Fatalf("cmd = %q, want explorer.exe", cmd)
	}
	if len(args) != 1 {
		t.Fatalf("args len = %d, want 1", len(args))
	}
	if args[0] != `\\DOSFS01\users\lindsay.townsend\Documents\9015-038-003-formatted.xlsx` {
		t.Fatalf("arg = %q", args[0])
	}
}

func TestOpenPathCommandUnsupported(t *testing.T) {
	if _, _, err := openPathCommand("plan9", "/tmp/file.xlsx"); err == nil {
		t.Fatal("expected unsupported OS error")
	}
}
