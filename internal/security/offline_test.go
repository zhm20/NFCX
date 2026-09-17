package security_test

import (
	"os"
	"path/filepath"
	"runtime"
	"strings"
	"testing"
)

func TestRuntimeSourceHasNoNetworkOrTelemetryHooks(t *testing.T) {
	_, current, _, ok := runtime.Caller(0)
	if !ok {
		t.Fatal("cannot locate repository root")
	}
	root := filepath.Clean(filepath.Join(filepath.Dir(current), "..", ".."))
	forbidden := []string{
		"net/" + "http",
		"telemetry." + "nfcx.tools",
		"api.github.com/" + "repos/",
		"Browser" + "OpenURL",
		"Track" + "Telemetry",
		"CheckFor" + "Updates",
	}
	scanRoots := []string{"app", "internal", filepath.Join("frontend", "src")}
	for _, relativeRoot := range scanRoots {
		base := filepath.Join(root, relativeRoot)
		err := filepath.WalkDir(base, func(path string, entry os.DirEntry, walkErr error) error {
			if walkErr != nil {
				return walkErr
			}
			if entry.IsDir() {
				return nil
			}
			if filepath.Clean(path) == filepath.Clean(current) {
				return nil
			}
			ext := strings.ToLower(filepath.Ext(path))
			if ext != ".go" && ext != ".ts" && ext != ".js" {
				return nil
			}
			data, err := os.ReadFile(path)
			if err != nil {
				return err
			}
			text := string(data)
			for _, token := range forbidden {
				if strings.Contains(text, token) {
					t.Errorf("runtime source %s contains forbidden outbound/telemetry token %q", path, token)
				}
			}
			return nil
		})
		if err != nil {
			t.Fatal(err)
		}
	}
	for _, removed := range []string{filepath.Join(root, "app", "telemetry.go"), filepath.Join(root, "internal", "telemetry")} {
		if _, err := os.Stat(removed); !os.IsNotExist(err) {
			t.Errorf("removed telemetry path still exists: %s", removed)
		}
	}
}
