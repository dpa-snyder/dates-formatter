package main

import "testing"

func TestDefaultSettingsUseManagedUpdatePath(t *testing.T) {
	settings := defaultSettings()
	if settings.UpdateFolder != defaultUpdatePath {
		t.Fatalf("UpdateFolder = %q, want %q", settings.UpdateFolder, defaultUpdatePath)
	}
}
