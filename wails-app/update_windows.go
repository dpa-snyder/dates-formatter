//go:build windows

package main

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"unsafe"

	"golang.org/x/sys/windows"
)

func supportsSelfUpdate() bool {
	return true
}

func executableMetadataVersion(path string) (string, error) {
	var zero windows.Handle
	size, err := windows.GetFileVersionInfoSize(path, &zero)
	if err != nil {
		return "", err
	}
	if size == 0 {
		return "", fmt.Errorf("no version metadata found in %s", path)
	}
	data := make([]byte, size)
	if err := windows.GetFileVersionInfo(path, 0, size, unsafe.Pointer(&data[0])); err != nil {
		return "", err
	}
	if version, err := queryVersionString(data, "ProductVersion"); err == nil && strings.TrimSpace(version) != "" {
		return strings.TrimSpace(version), nil
	}
	if version, err := queryVersionString(data, "FileVersion"); err == nil && strings.TrimSpace(version) != "" {
		return strings.TrimSpace(version), nil
	}
	return queryFixedFileVersion(data)
}

func queryVersionString(data []byte, key string) (string, error) {
	translations, err := versionTranslations(data)
	if err != nil || len(translations) == 0 {
		translations = []string{"040904b0"}
	}
	var lastErr error
	for _, translation := range translations {
		var value *uint16
		var valueLen uint32
		subBlock := fmt.Sprintf(`\StringFileInfo\%s\%s`, translation, key)
		err := windows.VerQueryValue(unsafe.Pointer(&data[0]), subBlock, unsafe.Pointer(&value), &valueLen)
		if err != nil {
			lastErr = err
			continue
		}
		if value == nil || valueLen == 0 {
			continue
		}
		return windows.UTF16PtrToString(value), nil
	}
	if lastErr != nil {
		return "", lastErr
	}
	return "", fmt.Errorf("%s not found", key)
}

func versionTranslations(data []byte) ([]string, error) {
	var ptr unsafe.Pointer
	var size uint32
	if err := windows.VerQueryValue(unsafe.Pointer(&data[0]), `\VarFileInfo\Translation`, unsafe.Pointer(&ptr), &size); err != nil {
		return nil, err
	}
	if ptr == nil || size < 4 {
		return nil, fmt.Errorf("translation table not found")
	}
	count := int(size / 4)
	values := unsafe.Slice((*uint16)(ptr), count*2)
	translations := make([]string, 0, count)
	for i := 0; i < count; i++ {
		lang := values[i*2]
		codePage := values[i*2+1]
		translations = append(translations, fmt.Sprintf("%04x%04x", lang, codePage))
	}
	return translations, nil
}

func queryFixedFileVersion(data []byte) (string, error) {
	var fixedInfo *windows.VS_FIXEDFILEINFO
	var fixedInfoLen uint32
	if err := windows.VerQueryValue(unsafe.Pointer(&data[0]), `\`, unsafe.Pointer(&fixedInfo), &fixedInfoLen); err != nil {
		return "", err
	}
	if fixedInfo == nil {
		return "", fmt.Errorf("fixed version metadata not found")
	}
	return fmt.Sprintf("%d.%d.%d.%d",
		fixedInfo.FileVersionMS>>16,
		fixedInfo.FileVersionMS&0xffff,
		fixedInfo.FileVersionLS>>16,
		fixedInfo.FileVersionLS&0xffff,
	), nil
}

func restartToApplyUpdate(stagedPath, targetPath string, pid int, expectedSHA256 string) error {
	helperDir := filepath.Dir(stagedPath)
	helperPath := filepath.Join(helperDir, "apply-date-formatter-update.ps1")
	script := fmt.Sprintf(`$ErrorActionPreference = 'Stop'
$ProcessIdToWait = %d
$Staged = %s
$Target = %s
$ExpectedHash = '%s'
try {
    Wait-Process -Id $ProcessIdToWait -Timeout 60 -ErrorAction SilentlyContinue
} catch {}
Start-Sleep -Milliseconds 500
$ActualHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $Staged).Hash.ToLowerInvariant()
if ($ActualHash -ne $ExpectedHash) { exit 2 }
Copy-Item -LiteralPath $Staged -Destination $Target -Force
Start-Process -FilePath $Target
Remove-Item -LiteralPath $Staged -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath $PSCommandPath -Force -ErrorAction SilentlyContinue
`, pid, powershellString(stagedPath), powershellString(targetPath), strings.ToLower(expectedSHA256))
	if err := os.WriteFile(helperPath, []byte(script), 0700); err != nil {
		return err
	}
	return exec.Command(
		"powershell.exe",
		"-NoProfile",
		"-ExecutionPolicy", "Bypass",
		"-WindowStyle", "Hidden",
		"-File", helperPath,
	).Start()
}

func powershellString(value string) string {
	return "'" + strings.ReplaceAll(value, "'", "''") + "'"
}
