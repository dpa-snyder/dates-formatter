package main

import (
	"fmt"
	"io"
	"os"
	"path/filepath"
	"regexp"
	"strconv"
	"strings"

	wailsruntime "github.com/wailsapp/wails/v2/pkg/runtime"
)

const (
	updateExecutableName = "date-formatter.exe"
	defaultUpdatePath    = `X:\Apps\` + updateExecutableName
)

type pendingUpdate struct {
	sourcePath       string
	stagedPath       string
	targetPath       string
	availableVersion string
}

type exeVersionReader func(path string) (string, error)

func updateExecutablePath(path string) string {
	rawPath := strings.TrimSpace(path)
	if rawPath == "" {
		return ""
	}
	trimmedPath := strings.TrimRight(rawPath, `/\`)
	if strings.EqualFold(pathBase(trimmedPath), updateExecutableName) {
		return trimmedPath
	}
	usesWindowsSeparators := strings.Contains(rawPath, `\`)
	folder := trimmedPath
	if strings.HasSuffix(folder, ":") || usesWindowsSeparators {
		return folder + `\` + updateExecutableName
	}
	return filepath.Join(folder, updateExecutableName)
}

func pathBase(path string) string {
	i := strings.LastIndexAny(path, `/\`)
	if i < 0 {
		return path
	}
	return path[i+1:]
}

func checkUpdateCandidate(currentVersion, folder string, readVersion exeVersionReader) (UpdateCheckResult, error) {
	result := UpdateCheckResult{
		CurrentVersion: currentVersion,
	}
	sourcePath := updateExecutablePath(folder)
	if sourcePath == "" {
		result.Message = "Update folder is not configured."
		return result, nil
	}
	result.SourcePath = sourcePath

	availableVersion, err := readVersion(sourcePath)
	if err != nil {
		result.Message = err.Error()
		return result, err
	}
	result.AvailableVersion = availableVersion
	if !isNewerVersion(currentVersion, availableVersion) {
		result.Message = "No newer update found."
		return result, nil
	}
	result.UpdateAvailable = true
	result.RestartRequired = true
	result.Message = "A newer Date Formatter is ready to install."
	return result, nil
}

func stageUpdateExecutable(sourcePath string) (string, error) {
	cacheDir, err := os.UserCacheDir()
	if err != nil || strings.TrimSpace(cacheDir) == "" {
		cacheDir = os.TempDir()
	}
	stageDir := filepath.Join(cacheDir, "date-formatter", "updates")
	if err := os.MkdirAll(stageDir, 0700); err != nil {
		return "", err
	}
	stagedPath := filepath.Join(stageDir, updateExecutableName)
	if err := copyFile(sourcePath, stagedPath); err != nil {
		return "", err
	}
	return stagedPath, nil
}

func copyFile(sourcePath, targetPath string) error {
	source, err := os.Open(sourcePath)
	if err != nil {
		return err
	}
	defer source.Close()

	targetDir := filepath.Dir(targetPath)
	temp, err := os.CreateTemp(targetDir, updateExecutableName+".*.tmp")
	if err != nil {
		return err
	}
	tempPath := temp.Name()
	cleanup := true
	defer func() {
		if cleanup {
			_ = os.Remove(tempPath)
		}
	}()

	if _, err := io.Copy(temp, source); err != nil {
		_ = temp.Close()
		return err
	}
	if err := temp.Chmod(0700); err != nil {
		_ = temp.Close()
		return err
	}
	if err := temp.Close(); err != nil {
		return err
	}
	_ = os.Remove(targetPath)
	if err := os.Rename(tempPath, targetPath); err != nil {
		return err
	}
	cleanup = false
	return nil
}

func isNewerVersion(current, candidate string) bool {
	currentParts, ok := parseVersionParts(current)
	if !ok {
		return false
	}
	candidateParts, ok := parseVersionParts(candidate)
	if !ok {
		return false
	}
	maxLen := len(currentParts)
	if len(candidateParts) > maxLen {
		maxLen = len(candidateParts)
	}
	for i := 0; i < maxLen; i++ {
		currentPart := 0
		candidatePart := 0
		if i < len(currentParts) {
			currentPart = currentParts[i]
		}
		if i < len(candidateParts) {
			candidatePart = candidateParts[i]
		}
		if candidatePart > currentPart {
			return true
		}
		if candidatePart < currentPart {
			return false
		}
	}
	return false
}

func parseVersionParts(version string) ([]int, bool) {
	version = strings.TrimSpace(strings.TrimPrefix(version, "v"))
	if version == "" {
		return nil, false
	}
	parts := regexp.MustCompile(`[.-]`).Split(version, -1)
	nums := make([]int, 0, len(parts))
	for _, part := range parts {
		if part == "" {
			return nil, false
		}
		n, err := strconv.Atoi(part)
		if err != nil {
			return nil, false
		}
		nums = append(nums, n)
	}
	return nums, len(nums) > 0
}

// CheckForUpdate checks the configured shared folder for date-formatter.exe.
func (a *App) CheckForUpdate() (UpdateCheckResult, error) {
	if !supportsSelfUpdate() {
		return UpdateCheckResult{
			CurrentVersion: version,
			Message:        "Automatic updates are supported on Windows only.",
		}, nil
	}
	result, err := checkUpdateCandidate(version, a.settings.UpdateFolder, executableMetadataVersion)
	if err != nil || !result.UpdateAvailable {
		return result, err
	}

	targetPath, err := os.Executable()
	if err != nil {
		return result, err
	}
	stagedPath, err := stageUpdateExecutable(result.SourcePath)
	if err != nil {
		return result, err
	}
	result.StagedPath = stagedPath

	a.updateMu.Lock()
	a.pendingUpdate = &pendingUpdate{
		sourcePath:       result.SourcePath,
		stagedPath:       stagedPath,
		targetPath:       targetPath,
		availableVersion: result.AvailableVersion,
	}
	a.updateMu.Unlock()

	return result, nil
}

// RestartToApplyUpdate quits the app and lets a short-lived helper replace the running EXE.
func (a *App) RestartToApplyUpdate() error {
	a.updateMu.Lock()
	pending := a.pendingUpdate
	a.updateMu.Unlock()
	if pending == nil {
		return fmt.Errorf("no update is ready")
	}
	if pending.stagedPath == "" {
		return fmt.Errorf("no staged update is ready")
	}
	if err := restartToApplyUpdate(pending.stagedPath, pending.targetPath, os.Getpid()); err != nil {
		return err
	}
	wailsruntime.Quit(a.ctx)
	return nil
}
