package main

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"runtime"
	"strings"

	wailsruntime "github.com/wailsapp/wails/v2/pkg/runtime"
)

const appVersion = "0.1.0"

// App is the main application struct bound to the Wails runtime.
type App struct {
	ctx        context.Context
	settings   Settings
	cancelProc context.CancelFunc
}

// NewApp creates a new App.
func NewApp() *App {
	return &App{}
}

func (a *App) startup(ctx context.Context) {
	a.ctx = ctx
	a.settings = a.loadSettings()
}

func (a *App) shutdown(ctx context.Context) {
	a.saveSettings(a.settings)
}

// ── Bound methods ──────────────────────────────────────────────────────────────

// PickFile opens a native file dialog and returns the selected path.
// Returns "" if the user cancels.
func (a *App) PickFile() string {
	path, err := wailsruntime.OpenFileDialog(a.ctx, wailsruntime.OpenDialogOptions{
		Title: "Select spreadsheet",
		Filters: []wailsruntime.FileFilter{
			{DisplayName: "Spreadsheets", Pattern: "*.xlsx;*.csv"},
			{DisplayName: "Excel (*.xlsx)", Pattern: "*.xlsx"},
			{DisplayName: "CSV (*.csv)", Pattern: "*.csv"},
		},
	})
	if err != nil {
		return ""
	}
	return path
}

// OpenPath opens the given file or folder in the OS file manager.
func (a *App) OpenPath(path string) {
	wailsruntime.BrowserOpenURL(a.ctx, "file://"+path)
}

// GetColumns loads the file at path and returns column names, row count,
// and a list of columns that look like they contain dates (T-013).
func (a *App) GetColumns(path string) (ColumnsResult, error) {
	return GetColumns(path)
}

// StartProcess begins conversion in a background goroutine.
// Events emitted:
//   "process:progress" → ProcessProgress
//   "process:done"     → ProcessResult
//   "process:error"    → string
//   "process:log"      → string
func (a *App) StartProcess(opts ProcessOptions) {
	if a.cancelProc != nil {
		a.cancelProc()
	}
	ctx, cancel := context.WithCancel(a.ctx)
	a.cancelProc = cancel

	go func() {
		defer cancel()

		wailsruntime.EventsEmit(a.ctx, "process:log",
			fmt.Sprintf("Starting: %d column(s), mode %d", len(opts.Columns), opts.Mode))

		progress := func(row, total int, column string, flagged int) {
			wailsruntime.EventsEmit(a.ctx, "process:progress", ProcessProgress{
				Row:     row,
				Total:   total,
				Column:  column,
				Flagged: flagged,
			})
		}

		result, err := ProcessFile(ctx, opts, progress)
		if err != nil {
			if ctx.Err() != nil {
				wailsruntime.EventsEmit(a.ctx, "process:log", "Cancelled.")
			} else {
				wailsruntime.EventsEmit(a.ctx, "process:error", err.Error())
			}
			return
		}

		a.addRecentFile(opts.FilePath)
		wailsruntime.EventsEmit(a.ctx, "process:log",
			fmt.Sprintf("Done. %d rows, %d flagged → %s",
				result.RowsProcessed, result.FlaggedRows, result.OutputPath))
		wailsruntime.EventsEmit(a.ctx, "process:done", result)
	}()
}

// CancelProcess cancels a running conversion.
func (a *App) CancelProcess() {
	if a.cancelProc != nil {
		a.cancelProc()
		a.cancelProc = nil
	}
}

// GetSettings returns the current persisted settings.
func (a *App) GetSettings() Settings {
	return a.settings
}

// SaveSettings persists settings to disk.
func (a *App) SaveSettings(s Settings) {
	a.settings = s
	a.saveSettings(s)
}

// GetAppVersion returns the app version string.
func (a *App) GetAppVersion() string {
	return appVersion
}

// ── Settings persistence ───────────────────────────────────────────────────────

func settingsPath() string {
	var base string
	switch runtime.GOOS {
	case "windows":
		base = os.Getenv("APPDATA")
	case "darwin":
		home, _ := os.UserHomeDir()
		base = filepath.Join(home, "Library", "Application Support")
	default:
		home, _ := os.UserHomeDir()
		base = filepath.Join(home, ".config")
	}
	return filepath.Join(base, "date-formatter", "settings.json")
}

func (a *App) loadSettings() Settings {
	defaults := Settings{
		Theme:          "system",
		LastMode:       ModeAE,
		LastOutputMode: "overwrite",
		RecentFiles:    []string{},
		WindowWidth:    1020,
		WindowHeight:   720,
	}
	data, err := os.ReadFile(settingsPath())
	if err != nil {
		return defaults
	}
	var s Settings
	if err := json.Unmarshal(data, &s); err != nil {
		return defaults
	}
	if s.RecentFiles == nil {
		s.RecentFiles = []string{}
	}
	return s
}

func (a *App) saveSettings(s Settings) {
	path := settingsPath()
	if err := os.MkdirAll(filepath.Dir(path), 0755); err != nil {
		return
	}
	data, err := json.MarshalIndent(s, "", "  ")
	if err != nil {
		return
	}
	_ = os.WriteFile(path, data, 0644)
}

// AddRecentFile prepends path to the recent files list (max 5).
func (a *App) addRecentFile(path string) {
	path = strings.TrimSpace(path)
	if path == "" {
		return
	}
	files := []string{path}
	for _, f := range a.settings.RecentFiles {
		if f != path {
			files = append(files, f)
		}
		if len(files) >= 5 {
			break
		}
	}
	a.settings.RecentFiles = files
	a.saveSettings(a.settings)
}
