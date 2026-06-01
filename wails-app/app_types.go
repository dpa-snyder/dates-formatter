package main

// Mode represents the conversion mode.
type Mode int

const (
	ModeSingle Mode = iota
	ModeAE
	ModeDC
)

// ProcessOptions is passed from the frontend to StartProcess.
type ProcessOptions struct {
	FilePath          string   `json:"filePath"`
	Columns           []string `json:"columns"`
	Mode              Mode     `json:"mode"`
	OutputMode        string   `json:"outputMode"` // "overwrite" | "copy"
	YYOverrideEnabled bool     `json:"yyOverrideEnabled"`
	YYPrefix          string   `json:"yyPrefix"`
}

// ColumnsResult is returned by GetColumns.
type ColumnsResult struct {
	Columns      []string `json:"columns"`
	RowCount     int      `json:"rowCount"`
	DateyColumns []string `json:"dateyColumns"` // T-013: likely-date columns
}

// ProcessProgress is emitted as event "process:progress" during a run.
type ProcessProgress struct {
	Row     int    `json:"row"`
	Total   int    `json:"total"`
	Column  string `json:"column"`
	Flagged int    `json:"flagged"`
}

// ProcessResult is emitted as event "process:done" when a run completes.
type ProcessResult struct {
	RowsProcessed int      `json:"rowsProcessed"`
	FlaggedRows   int      `json:"flaggedRows"`
	OutputPath    string   `json:"outputPath"`
	Columns       []string `json:"columns"`
}

// Settings mirrors the keys in dates-formatter-settings.json for forward-compat.
type Settings struct {
	Theme             string   `json:"theme"` // "light" | "dark" | "system"
	LastMode          Mode     `json:"lastMode"`
	LastOutputMode    string   `json:"lastOutputMode"` // "overwrite" | "copy"
	RecentFiles       []string `json:"recentFiles"`    // last 5 paths
	WindowWidth       int      `json:"windowWidth"`
	WindowHeight      int      `json:"windowHeight"`
	YYOverrideEnabled bool     `json:"yyOverrideEnabled"`
	YYPrefix          string   `json:"yyPrefix"`
}
