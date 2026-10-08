//go:build darwin || linux

package main

import (
	"fmt"
	"os"
	"syscall"

	"golang.org/x/sys/unix"
)

func validatePrivateOutputDirectory(info os.FileInfo) error {
	metadata, ok := info.Sys().(*syscall.Stat_t)
	if !ok || !info.IsDir() || int(metadata.Uid) != os.Getuid() || info.Mode().Perm()&0077 != 0 {
		return fmt.Errorf("temporary output directory is not private")
	}
	return nil
}

func openStagedOutput(temp *outputTemp) (*os.File, error) {
	return temp.root.OpenFile("output", os.O_RDWR|os.O_CREATE|os.O_EXCL, 0600)
}

func preserveOutputPermissions(file *os.File, info os.FileInfo) error {
	if info == nil {
		return nil
	}
	metadata, ok := info.Sys().(*syscall.Stat_t)
	if !ok {
		return fmt.Errorf("cannot preserve output ownership")
	}
	if err := file.Chown(int(metadata.Uid), int(metadata.Gid)); err != nil {
		return err
	}
	return file.Chmod(info.Mode().Perm())
}

func publishStagedOutput(temp *outputTemp, target string) error {
	return unix.Renameat(int(temp.handle.Fd()), "output", int(temp.directory.handle.Fd()), target)
}

func discardStagedOutput(temp *outputTemp) { _ = temp.root.Remove("output") }
