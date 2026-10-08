package main

import (
	"context"
	"crypto/rand"
	"fmt"
	"os"
	"path/filepath"
)

type outputDirectory struct {
	root   *os.Root
	handle *os.File
}

func openOutputDirectory(path string) (*outputDirectory, error) {
	root, err := os.OpenRoot(filepath.Dir(path))
	if err != nil {
		return nil, err
	}
	handle, err := root.Open(".")
	if err != nil {
		root.Close()
		return nil, err
	}
	return &outputDirectory{root: root, handle: handle}, nil
}

func (d *outputDirectory) close() {
	_ = d.handle.Close()
	_ = d.root.Close()
}

type outputTemp struct {
	file          *os.File
	root          *os.Root
	handle        *os.File
	directory     *outputDirectory
	directoryName string
	directoryInfo os.FileInfo
	published     bool
}

func createOutputTemp(directory *outputDirectory, target string) (*outputTemp, error) {
	info, err := directory.root.Lstat(filepath.Base(target))
	if err != nil && !os.IsNotExist(err) {
		return nil, err
	}
	if err == nil && !info.Mode().IsRegular() {
		return nil, fmt.Errorf("output must be a regular file, not a link or directory")
	}
	var nonce [16]byte
	if _, err := rand.Read(nonce[:]); err != nil {
		return nil, err
	}
	name := fmt.Sprintf(".date-formatter-%x", nonce)
	if err := directory.root.Mkdir(name, 0700); err != nil {
		return nil, err
	}
	temp := &outputTemp{directory: directory, directoryName: name}
	// The retained child root keeps publication anchored even if an attacker
	// renames the private directory and substitutes its old pathname.
	temp.root, err = directory.root.OpenRoot(name)
	if err != nil {
		_ = directory.root.Remove(name)
		return nil, err
	}
	temp.handle, err = temp.root.Open(".")
	if err != nil {
		temp.close()
		return nil, err
	}
	temp.directoryInfo, err = temp.handle.Stat()
	if err == nil {
		err = validatePrivateOutputDirectory(temp.directoryInfo)
	}
	if err != nil {
		temp.close()
		return nil, err
	}
	temp.file, err = openStagedOutput(temp)
	if err != nil {
		temp.close()
		return nil, err
	}
	if err := preserveOutputPermissions(temp.file, info); err != nil {
		temp.close()
		return nil, err
	}
	return temp, nil
}

func (t *outputTemp) close() {
	if t.file != nil {
		if !t.published {
			discardStagedOutput(t)
		}
		// On Windows the exclusive handle is closed only after publication.
		_ = t.file.Close()
	}
	if t.root != nil {
		_ = t.root.Close()
	}
	if t.handle != nil {
		_ = t.handle.Close()
	}
	if info, err := t.directory.root.Lstat(t.directoryName); err == nil &&
		t.directoryInfo != nil && os.SameFile(info, t.directoryInfo) {
		_ = t.directory.root.Remove(t.directoryName)
	}
}

func writeOutput(ctx context.Context, path string, headers []string, rows [][]string) error {
	directory, err := openOutputDirectory(path)
	if err != nil {
		return err
	}
	defer directory.close()
	return writeOutputInDirectory(ctx, path, headers, rows, directory)
}

func writeOutputInDirectory(ctx context.Context, path string, headers []string, rows [][]string, directory *outputDirectory) error {
	if err := ctx.Err(); err != nil {
		return err
	}
	temp, err := createOutputTemp(directory, path)
	if err != nil {
		return err
	}
	defer temp.close()
	if isCSV(path) {
		err = writeCSV(temp.file, headers, rows)
	} else {
		err = writeXLSX(temp.file, headers, rows)
	}
	if err != nil {
		return err
	}
	if err := temp.file.Sync(); err != nil {
		return err
	}
	if err := ctx.Err(); err != nil {
		return err
	}
	target := filepath.Base(path)
	if info, err := directory.root.Lstat(target); err == nil {
		if !info.Mode().IsRegular() {
			return fmt.Errorf("output must be a regular file, not a link or directory")
		}
	} else if !os.IsNotExist(err) {
		return err
	}
	// Native rename replaces the destination entry atomically, refuses
	// directories, and never moves the original away to a backup pathname.
	if err := publishStagedOutput(temp, target); err != nil {
		return err
	}
	temp.published = true
	return nil
}
