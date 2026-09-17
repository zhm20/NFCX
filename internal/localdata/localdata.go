// Package localdata centralizes filesystem protections for NFC credentials and card data.
package localdata

import (
	"errors"
	"fmt"
	"os"
	"path/filepath"
)

const (
	PrivateDirPerm    os.FileMode = 0o700
	SensitiveFilePerm os.FileMode = 0o600
)

// EnsurePrivateDir is for application-owned directories only. It must not be
// used on arbitrary user-selected parent directories such as Desktop.
func EnsurePrivateDir(path string) error {
	if path == "" || path == "." {
		return errors.New("private directory path is required")
	}
	if err := os.MkdirAll(path, PrivateDirPerm); err != nil {
		return err
	}
	if err := os.Chmod(path, PrivateDirPerm); err != nil {
		return fmt.Errorf("restrict private directory: %w", err)
	}
	return nil
}

// WriteAppFileAtomic writes application-owned sensitive state and restricts
// both its parent directory and final file where the operating system supports it.
func WriteAppFileAtomic(path string, data []byte) error {
	if path == "" {
		return errors.New("sensitive file path is required")
	}
	if err := EnsurePrivateDir(filepath.Dir(path)); err != nil {
		return err
	}
	return writeAtomic(path, data)
}

// WriteSensitiveFileAtomic protects a user-selected output file without
// changing permissions on its existing parent directory.
func WriteSensitiveFileAtomic(path string, data []byte) error {
	if path == "" {
		return errors.New("sensitive file path is required")
	}
	return writeAtomic(path, data)
}

// HardenFile restricts an existing sensitive regular file to the current user
// on platforms that expose POSIX-style permissions.
func HardenFile(path string) error {
	info, err := os.Stat(path)
	if err != nil {
		return err
	}
	if !info.Mode().IsRegular() {
		return fmt.Errorf("sensitive path is not a regular file: %s", path)
	}
	if err := os.Chmod(path, SensitiveFilePerm); err != nil {
		return fmt.Errorf("restrict sensitive file: %w", err)
	}
	return nil
}

func writeAtomic(path string, data []byte) error {
	directory := filepath.Dir(path)
	temporary, err := os.CreateTemp(directory, ".nfcx-sensitive-*")
	if err != nil {
		return err
	}
	temporaryPath := temporary.Name()
	keep := false
	defer func() {
		_ = temporary.Close()
		if !keep {
			_ = os.Remove(temporaryPath)
		}
	}()
	if err := temporary.Chmod(SensitiveFilePerm); err != nil {
		return err
	}
	if _, err := temporary.Write(data); err != nil {
		return err
	}
	if err := temporary.Sync(); err != nil {
		return err
	}
	if err := temporary.Close(); err != nil {
		return err
	}
	if err := os.Rename(temporaryPath, path); err != nil {
		return err
	}
	keep = true
	return HardenFile(path)
}
