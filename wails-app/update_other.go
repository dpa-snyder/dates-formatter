//go:build !windows

package main

import "fmt"

func supportsSelfUpdate() bool {
	return false
}

func executableMetadataVersion(path string) (string, error) {
	return "", fmt.Errorf("EXE metadata updates are supported on Windows only")
}

func restartToApplyUpdate(stagedPath, targetPath string, pid int) error {
	return fmt.Errorf("automatic updates are supported on Windows only")
}
