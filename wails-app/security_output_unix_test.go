//go:build darwin || linux

package main

import (
	"context"
	"os"
	"path/filepath"
	"syscall"
	"testing"
)

func TestOverwritePreservesOwningGroup(t *testing.T) {
	groups, err := os.Getgroups()
	if err != nil {
		t.Fatal(err)
	}
	group := -1
	for _, candidate := range groups {
		if candidate != os.Getgid() {
			group = candidate
			break
		}
	}
	if group < 0 {
		t.Skip("No supplementary group available")
	}
	path := filepath.Join(t.TempDir(), "output.csv")
	if err := os.WriteFile(path, []byte("original"), 0640); err != nil {
		t.Fatal(err)
	}
	if err := os.Chown(path, os.Getuid(), group); err != nil {
		t.Fatal(err)
	}
	if err := os.Chmod(path, 0640); err != nil {
		t.Fatal(err)
	}
	if err := writeOutput(context.Background(), path, []string{"Date"}, [][]string{{"1962"}}); err != nil {
		t.Fatal(err)
	}
	info, err := os.Stat(path)
	if err != nil {
		t.Fatal(err)
	}
	metadata := info.Sys().(*syscall.Stat_t)
	if int(metadata.Uid) != os.Getuid() || int(metadata.Gid) != group || info.Mode().Perm() != 0640 {
		t.Fatalf("ownership or permission changed: uid=%d gid=%d mode=%o", metadata.Uid, metadata.Gid, info.Mode().Perm())
	}
}
