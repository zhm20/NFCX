package localdata_test

import (
	"os"
	"path/filepath"
	"runtime"
	"testing"

	"github.com/BennyThink/NFCX/internal/localdata"
)

func TestWriteAppFileAtomicUsesPrivatePermissions(t *testing.T) {
	root := filepath.Join(t.TempDir(), "private")
	path := filepath.Join(root, "keys.json")
	if err := localdata.WriteAppFileAtomic(path, []byte("secret\n")); err != nil {
		t.Fatal(err)
	}
	if got, err := os.ReadFile(path); err != nil || string(got) != "secret\n" {
		t.Fatalf("read sensitive file: %q, %v", got, err)
	}
	if runtime.GOOS != "windows" {
		dirInfo, err := os.Stat(root)
		if err != nil {
			t.Fatal(err)
		}
		if dirInfo.Mode().Perm() != 0o700 {
			t.Fatalf("directory permissions = %v, want 0700", dirInfo.Mode().Perm())
		}
		fileInfo, err := os.Stat(path)
		if err != nil {
			t.Fatal(err)
		}
		if fileInfo.Mode().Perm() != 0o600 {
			t.Fatalf("file permissions = %v, want 0600", fileInfo.Mode().Perm())
		}
	}
}

func TestWriteSensitiveFileDoesNotChangeParentPermissions(t *testing.T) {
	root := t.TempDir()
	if runtime.GOOS != "windows" {
		if err := os.Chmod(root, 0o755); err != nil {
			t.Fatal(err)
		}
	}
	path := filepath.Join(root, "card.mfd")
	if err := localdata.WriteSensitiveFileAtomic(path, []byte("dump")); err != nil {
		t.Fatal(err)
	}
	if runtime.GOOS != "windows" {
		dirInfo, _ := os.Stat(root)
		fileInfo, _ := os.Stat(path)
		if dirInfo.Mode().Perm() != 0o755 {
			t.Fatalf("user-selected parent permissions changed to %v", dirInfo.Mode().Perm())
		}
		if fileInfo.Mode().Perm() != 0o600 {
			t.Fatalf("dump permissions = %v, want 0600", fileInfo.Mode().Perm())
		}
	}
}
