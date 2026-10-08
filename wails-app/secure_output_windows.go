//go:build windows

package main

import (
	"os"
	"unsafe"

	"golang.org/x/sys/windows"
)

func validatePrivateOutputDirectory(info os.FileInfo) error { return nil }

func openStagedOutput(temp *outputTemp) (*os.File, error) {
	name, err := windows.NewNTUnicodeString("output")
	if err != nil {
		return nil, err
	}
	attributes := windows.OBJECT_ATTRIBUTES{
		RootDirectory: windows.Handle(temp.handle.Fd()), ObjectName: name, Attributes: windows.OBJ_CASE_INSENSITIVE,
	}
	attributes.Length = uint32(unsafe.Sizeof(attributes))
	var handle windows.Handle
	var status windows.IO_STATUS_BLOCK
	err = windows.NtCreateFile(&handle,
		windows.FILE_GENERIC_READ|windows.FILE_GENERIC_WRITE|windows.DELETE,
		&attributes, &status, nil, windows.FILE_ATTRIBUTE_NORMAL, 0,
		windows.FILE_CREATE, windows.FILE_NON_DIRECTORY_FILE|windows.FILE_SYNCHRONOUS_IO_NONALERT|windows.FILE_OPEN_REPARSE_POINT,
		0, 0)
	if err != nil {
		return nil, err
	}
	// No sharing: the entry and contents cannot be substituted while this
	// descriptor is retained, including the final publication transition.
	return os.NewFile(uintptr(handle), "output"), nil
}

func preserveOutputPermissions(file *os.File, info os.FileInfo) error {
	if info == nil {
		return nil
	}
	return file.Chmod(info.Mode().Perm())
}

func publishStagedOutput(temp *outputTemp, target string) error {
	name, err := windows.UTF16FromString(target)
	if err != nil {
		return err
	}
	type renameInfo struct {
		ReplaceIfExists byte
		RootDirectory   windows.Handle
		FileNameLength  uint32
		FileName        [1]uint16
	}
	size := int(unsafe.Offsetof(renameInfo{}.FileName)) + (len(name)-1)*2
	buffer := make([]byte, size)
	info := (*renameInfo)(unsafe.Pointer(&buffer[0]))
	info.ReplaceIfExists = 1
	info.RootDirectory = windows.Handle(temp.directory.handle.Fd())
	info.FileNameLength = uint32((len(name) - 1) * 2)
	copy(unsafe.Slice(&info.FileName[0], len(name)-1), name[:len(name)-1])
	var status windows.IO_STATUS_BLOCK
	// NtSetInformationFile supports a rooted destination and the open source
	// handle. No pathname-based fallback is safe at this boundary.
	return windows.NtSetInformationFile(windows.Handle(temp.file.Fd()), &status,
		&buffer[0], uint32(size), windows.FileRenameInformation)
}

func discardStagedOutput(temp *outputTemp) {
	// Clearing the staged file's read-only flag keeps failed overwrites from
	// leaving output behind. This operates on the retained handle, not a path.
	_ = temp.file.Chmod(0600)
	delete := byte(1)
	var status windows.IO_STATUS_BLOCK
	_ = windows.NtSetInformationFile(windows.Handle(temp.file.Fd()), &status, &delete, 1, windows.FileDispositionInformation)
}
