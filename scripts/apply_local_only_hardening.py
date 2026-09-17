#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def write(path: str, content: str) -> None:
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def replace_exact(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise SystemExit(f"expected text not found: {label}")
    return text.replace(old, new, 1)


def sub_once(text: str, pattern: str, replacement: str, label: str, flags: int = 0) -> str:
    updated, count = re.subn(pattern, lambda _match: replacement, text, count=1, flags=flags)
    if count != 1:
        raise SystemExit(f"expected exactly one regex match for {label}, got {count}")
    return updated


# 1-4. Remove runtime telemetry and online update checking.
service = read("app/service.go")
service = replace_exact(service, '\truntimebundle "github.com/BennyThink/NFCX/internal/runtime"\n\t"github.com/BennyThink/NFCX/internal/telemetry"\n', '\truntimebundle "github.com/BennyThink/NFCX/internal/runtime"\n', "service telemetry import")
service = replace_exact(service, '\tdialogs          fileDialogs\n\ttelemetry        *telemetry.Client\n\ttelemetryStore   *telemetry.Store\n', '\tdialogs          fileDialogs\n', "service telemetry fields")
service = replace_exact(service, '\tkeyStorePath := ""\n\tuidBackupRoot := ""\n\ttelemetryPath := ""\n', '\tkeyStorePath := ""\n\tuidBackupRoot := ""\n', "service telemetry path declaration")
service = replace_exact(service, '\t\tuidBackupRoot = filepath.Join(configRoot, "NFCX", "uid-backups")\n\t\ttelemetryPath = filepath.Join(configRoot, "NFCX", "telemetry.json")\n\t\t_ = keyStore.Load(keyStorePath)\n\t}\n\ttelemetryStore := telemetry.NewStore(telemetryPath)\n\tif telemetryPath != "" {\n\t\t_ = telemetryStore.Load()\n\t}\n', '\t\tuidBackupRoot = filepath.Join(configRoot, "NFCX", "uid-backups")\n\t\t_ = keyStore.Load(keyStorePath)\n\t}\n', "service telemetry initialization")
service = replace_exact(service, '\t\tdialogs:          noFileDialogs{},\n\t\ttelemetry:        telemetry.NewClient(telemetryStore),\n\t\ttelemetryStore:   telemetryStore,\n', '\t\tdialogs:          noFileDialogs{},\n', "service telemetry wiring")
write("app/service.go", service)

bindings = read("app/bindings.go")
bindings = replace_exact(bindings, 'import "github.com/BennyThink/NFCX/internal/diagnostic"\nimport "github.com/BennyThink/NFCX/internal/telemetry"\n', 'import "github.com/BennyThink/NFCX/internal/diagnostic"\n', "bindings telemetry import")
bindings = sub_once(
    bindings,
    r'\nfunc \(b \*Bindings\) GetTelemetrySettings\(\) TelemetrySettingsDTO \{.*?func \(b \*Bindings\) CheckForUpdates\(\) \(telemetry\.UpdateResult, error\) \{\n\treturn b\.service\.CheckForUpdates\(\)\n\}\n',
    '\n',
    "bindings telemetry/update API",
    re.S,
)
write("app/bindings.go", bindings)

for path in [
    "app/telemetry.go",
    "internal/telemetry/telemetry.go",
    "internal/telemetry/telemetry_test.go",
    "docs/deployment.md",
    "docs/notes/14-telemetry.md",
    "docs/specs/14-telemetry.md",
]:
    target = ROOT / path
    if target.exists():
        target.unlink()
for directory in ["internal/telemetry", "telemetry-worker"]:
    target = ROOT / directory
    if target.exists():
        shutil.rmtree(target)

# 2, 4, 5, 6. Remove telemetry/update UI and all runtime external links; add sensitive-data confirmations.
main = read("frontend/src/main.ts")
main = replace_exact(
    main,
    '  EditBlockASCII, EditBlockHex, ExportKeyDictionary, GetDashboard, GetDiagnostics,\n  GetTelemetrySettings, SetTelemetryEnabled, TrackTelemetry, CheckForUpdates,\n',
    '  EditBlockASCII, EditBlockHex, ExportKeyDictionary, GetDashboard, GetDiagnostics,\n',
    "frontend telemetry imports",
)
main = replace_exact(main, 'import { BrowserOpenURL, EventsOn } from "../wailsjs/runtime/runtime";', 'import { EventsOn } from "../wailsjs/runtime/runtime";', "frontend BrowserOpenURL import")
main = replace_exact(main, 'interface TelemetrySettings { configured: boolean; enabled: boolean; }\ninterface UpdateResult { currentVersion: string; latestVersion: string; updateAvailable: boolean; url: string; }\n', '', "frontend telemetry/update types")
main = re.sub(r'\sdata-telemetry="[^"]+"', '', main)
main = sub_once(
    main,
    r'  <dialog class="modal compact-modal" id="about-modal">.*?  <dialog class="modal compact-modal" id="telemetry-consent-modal">.*?</dialog>`;',
    '  <dialog class="modal compact-modal" id="about-modal"><form method="dialog" class="modal-card"><header><h2 data-i18n="about.title"></h2><button class="close-button" value="cancel">×</button></header><div class="about-content"><p><strong>NFCX</strong> <span id="about-version"></span></p><p><span data-i18n="about.author"></span>: BennyThink · local hardening: zhm20</p><p class="privacy-note" data-i18n="about.local_only"></p><footer><button class="ghost-button" id="diagnostics-button" type="button" data-i18n="about.diagnostics"></button><button class="secondary-button" value="cancel" data-i18n="common.close"></button></footer></div></form></dialog>`;',
    "about/telemetry dialogs",
    re.S,
)
main = sub_once(
    main,
    r'^const diagnosticsModal = .*?;$',
    'const diagnosticsModal = el<HTMLDialogElement>("#diagnostics-modal"), diagnosticsContent = el<HTMLDivElement>("#diagnostics-content"), diagnosticsButton = el<HTMLButtonElement>("#diagnostics-button"), diagnosticsRefresh = el<HTMLButtonElement>("#diagnostics-refresh"), aboutModal = el<HTMLDialogElement>("#about-modal"), aboutButton = el<HTMLButtonElement>("#about-button"), aboutVersion = el<HTMLElement>("#about-version");',
    "frontend about DOM references",
    re.M,
)
main = sub_once(
    main,
    r'aboutButton\.addEventListener\("click", async \(\) => \{.*?root\.addEventListener\("click", \(event\) => \{.*?\}\);\n',
    'aboutButton.addEventListener("click", () => aboutModal.showModal());\n',
    "frontend telemetry/update listeners",
    re.S,
)
main = replace_exact(
    main,
    'el<HTMLButtonElement>("#export-keys-button").addEventListener("click", async (event) => { event.preventDefault(); try {',
    'el<HTMLButtonElement>("#export-keys-button").addEventListener("click", async (event) => { event.preventDefault(); if (!window.confirm(t("security.key_export_warning"))) return; try {',
    "key export warning",
)
main = replace_exact(
    main,
    'saveButton.addEventListener("click", async () => { try {',
    'saveButton.addEventListener("click", async () => { if (!window.confirm(t("security.dump_warning"))) return; try {',
    "dump save warning",
)
main = sub_once(
    main,
    r'async function boot\(\): Promise<void> \{.*?\}\nvoid boot\(\);',
    '''async function boot(): Promise<void> {
  refreshLanguage();
  applyTheme(storedTheme());
  try {
    const [dashboard, workspace, storedKeys] = await Promise.all([GetDashboard(), GetWorkbench(), GetKeyCatalog()]);
    recoverButton.title = "Automatically runs common keys, Darkside, Nested, Hardnested (as needed), and read verification";
    aboutVersion.textContent = `v${(await GetDiagnostics() as DiagnosticReport).build.version}`;
    renderDevices(dashboard.devices as Device[], dashboard.selectedDevice);
    renderConnection(dashboard.connection as Connection);
    renderCard(dashboard.card as Card);
    renderSectorKeys(dashboard.keys as SectorKey[]);
    renderWorkbench(workspace as Workbench);
    renderCatalog(storedKeys as KeyEntry[]);
  } catch (error) {
    appendLog(`Initialization failed: ${String(error)}`, undefined, "error");
  }
  try {
    renderDevices((await RefreshDevices()) as Device[]);
  } catch (error) {
    appendLog(`Reader enumeration failed: ${String(error)}`, undefined, "error");
  }
}
void boot();''',
    "frontend boot telemetry removal",
    re.S,
)
for forbidden in ["GetTelemetrySettings", "SetTelemetryEnabled", "TrackTelemetry", "CheckForUpdates", "telemetry-consent", "telemetry-toggle", "update-button", "BrowserOpenURL", "https://nfcx.tools", "https://github.com/BennyThink/NFCX"]:
    if forbidden in main:
        raise SystemExit(f"frontend runtime still contains forbidden outbound/telemetry token: {forbidden}")
write("frontend/src/main.ts", main)

# Locales: remove stale telemetry/update copy and document local-only/sensitive-data behavior.
for locale_path, values in [
    ("frontend/src/locales/en.json", {
        "about.local_only": "Local-only hardened fork: no telemetry, online update checks, or runtime network requests.",
        "security.dump_warning": "Dump files and NFCX sidecars may contain card UIDs, sector data, and recovered keys. Save only to a trusted local location. Continue?",
        "security.key_export_warning": "The exported dictionary contains NFC authentication keys in plaintext. Save it only to a trusted local location. Continue?",
        "keys.privacy": "Keys are displayed in full in this local tool, are not sent over the network, and app-owned key storage is restricted to the current user where the OS supports it.",
    }),
    ("frontend/src/locales/zh-CN.json", {
        "about.local_only": "本地安全加固版：不包含遥测、在线更新检查或运行时网络请求。",
        "security.dump_warning": "Dump 与 NFCX sidecar 可能包含卡片 UID、扇区数据和已恢复密钥。请仅保存到可信的本地位置。是否继续？",
        "security.key_export_warning": "导出的字典包含明文 NFC 认证密钥。请仅保存到可信的本地位置。是否继续？",
        "keys.privacy": "本地工具会完整显示密钥；密钥不会通过网络发送，应用自有密钥文件会在操作系统支持时限制为仅当前用户可访问。",
    }),
]:
    data = json.loads(read(locale_path))
    for key in list(data):
        if key.startswith("telemetry.") or key in {
            "about.check_updates", "about.checking_updates", "about.update_available",
            "about.up_to_date", "about.update_failed", "about.download",
        }:
            data.pop(key)
    data.update(values)
    write(locale_path, json.dumps(data, ensure_ascii=False, indent=2) + "\n")

# 6. Centralize sensitive local-data permissions for keys, dumps, and UID backups.
write("internal/localdata/localdata.go", r'''// Package localdata centralizes filesystem protections for NFC credentials and card data.
package localdata

import (
    "errors"
    "fmt"
    "os"
    "path/filepath"
)

const (
    PrivateDirPerm  os.FileMode = 0o700
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
''')

write("internal/localdata/localdata_test.go", r'''package localdata_test

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
''')

keys = read("internal/keys/store.go")
keys = replace_exact(keys, '\t"os"\n\t"path/filepath"\n', '\t"os"\n', "keys filepath import")
keys = replace_exact(keys, '\t"github.com/BennyThink/NFCX/internal/nfc"\n', '\t"github.com/BennyThink/NFCX/internal/localdata"\n\t"github.com/BennyThink/NFCX/internal/nfc"\n', "keys localdata import")
keys = sub_once(
    keys,
    r'\tif err := os\.MkdirAll\(filepath\.Dir\(path\), 0o700\); err != nil \{.*?\treturn os\.Rename\(temporaryPath, path\)\n',
    '\treturn localdata.WriteAppFileAtomic(path, append(encoded, \'\\n\'))\n',
    "keys secure persistence",
    re.S,
)
write("internal/keys/store.go", keys)

uid = read("internal/workflow/uid_backup.go")
uid = replace_exact(uid, '\t"time"\n)\n', '\t"time"\n\n\t"github.com/BennyThink/NFCX/internal/localdata"\n)\n', "UID localdata import")
uid = replace_exact(uid, '\tif err := os.MkdirAll(s.Root, 0o700); err != nil {\n\t\treturn "", err\n\t}\n\tif err := os.Chmod(s.Root, 0o700); err != nil {\n\t\treturn "", err\n\t}\n', '\tif err := localdata.EnsurePrivateDir(s.Root); err != nil {\n\t\treturn "", err\n\t}\n', "UID private directory")
uid = replace_exact(uid, '\tif err := os.Rename(temporaryPath, path); err != nil {\n\t\treturn "", err\n\t}\n\tkeep = true\n\treturn path, nil\n', '\tif err := os.Rename(temporaryPath, path); err != nil {\n\t\treturn "", err\n\t}\n\tkeep = true\n\tif err := localdata.HardenFile(path); err != nil {\n\t\t_ = os.Remove(path)\n\t\treturn "", err\n\t}\n\treturn path, nil\n', "UID final file hardening")
write("internal/workflow/uid_backup.go", uid)

dump = read("internal/workflow/dump_file.go")
dump = replace_exact(dump, '\t"os"\n\t"path/filepath"\n', '\t"os"\n', "dump filepath import")
dump = replace_exact(dump, '\t"github.com/BennyThink/NFCX/internal/mifare"\n', '\t"github.com/BennyThink/NFCX/internal/localdata"\n\t"github.com/BennyThink/NFCX/internal/mifare"\n', "dump localdata import")
dump = sub_once(
    dump,
    r'func atomicWriteFile\(path string, data \[\]byte\) error \{.*?\n\}\n\nfunc layoutName',
    'func atomicWriteFile(path string, data []byte) error {\n\treturn localdata.WriteSensitiveFileAtomic(path, data)\n}\n\nfunc layoutName',
    "dump sensitive writer",
    re.S,
)
write("internal/workflow/dump_file.go", dump)

# 7. Release runtime execution must validate against the release manifest hash.
locator = read("internal/runtime/locator.go")
locator = replace_exact(
    locator,
    '''\t\tif executable.SHA256 != "" {\n\t\t\tif err := verifyHash(resolvedPath, executable.SHA256); err != nil {\n\t\t\t\treturn "", fmt.Errorf("%s: %w", executable.ID, err)\n\t\t\t}\n\t\t}\n\t\treturn resolvedPath, nil\n''',
    '''\t\tif executable.SHA256 != "" {\n\t\t\tif err := verifyHash(resolvedPath, executable.SHA256); err != nil {\n\t\t\t\treturn "", fmt.Errorf("%s: %w", executable.ID, err)\n\t\t\t}\n\t\t} else {\n\t\t\tmanifestPath := filepath.Join(resolvedRoot, "manifest.json")\n\t\t\tif _, manifestErr := os.Stat(manifestPath); manifestErr == nil {\n\t\t\t\tif err := verifyManifestExecutable(resolvedRoot, resolvedPath); err != nil {\n\t\t\t\t\treturn "", fmt.Errorf("%s: %w", executable.ID, err)\n\t\t\t\t}\n\t\t\t} else if !errors.Is(manifestErr, os.ErrNotExist) {\n\t\t\t\treturn "", fmt.Errorf("inspect runtime manifest: %w", manifestErr)\n\t\t\t}\n\t\t}\n\t\treturn resolvedPath, nil\n''',
    "locator release-manifest enforcement",
)
locator = replace_exact(
    locator,
    'func validBaseName(name string) bool {',
    '''func verifyManifestExecutable(root, path string) error {\n\tmanifest, err := ReadManifest(filepath.Join(root, "manifest.json"))\n\tif err != nil {\n\t\treturn err\n\t}\n\trelative, err := filepath.Rel(root, path)\n\tif err != nil {\n\t\treturn err\n\t}\n\trelative = filepath.ToSlash(relative)\n\tfor _, entry := range manifest.Files {\n\t\tif entry.Path != relative {\n\t\t\tcontinue\n\t\t}\n\t\tif !entry.Executable {\n\t\t\treturn fmt.Errorf("%w: %s is not marked executable in runtime manifest", ErrInvalidManifest, relative)\n\t\t}\n\t\treturn verifyHash(path, entry.SHA256)\n\t}\n\treturn fmt.Errorf("%w: executable %s is not listed in runtime manifest", ErrHashMismatch, relative)\n}\n\nfunc validBaseName(name string) bool {''',
    "locator manifest helper",
)
write("internal/runtime/locator.go", locator)

locator_test = read("internal/runtime/locator_test.go")
locator_test += r'''

func TestLocatorUsesReleaseManifestWhenDescriptorHashIsEmpty(t *testing.T) {
    root := t.TempDir()
    name := "engine"
    if runtime.GOOS == "windows" {
        name += ".exe"
    }
    path := filepath.Join(root, name)
    contents := []byte("release-fixture")
    if err := os.WriteFile(path, contents, 0o755); err != nil {
        t.Fatal(err)
    }
    wanted := fmt.Sprintf("%x", sha256.Sum256(contents))
    manifest := runtimebundle.Manifest{
        SchemaVersion: runtimebundle.ManifestSchemaVersion,
        Platform: runtime.GOOS + "-" + runtime.GOARCH,
        NFCXVersion: "test",
        Commit: "test-commit",
        Files: []runtimebundle.ManifestFile{{Path: name, SHA256: wanted, Size: int64(len(contents)), Executable: true}},
    }
    if err := runtimebundle.WriteManifest(filepath.Join(root, "manifest.json"), manifest); err != nil {
        t.Fatal(err)
    }
    executable := runtimebundle.Executable{ID: "fixture", FileName: "engine", WindowsFileName: "engine.exe"}
    if _, err := runtimebundle.NewLocator(root).Resolve(executable); err != nil {
        t.Fatalf("resolve release executable: %v", err)
    }
    if err := os.WriteFile(path, []byte("tampered-runtime"), 0o755); err != nil {
        t.Fatal(err)
    }
    if _, err := runtimebundle.NewLocator(root).Resolve(executable); !errors.Is(err, runtimebundle.ErrHashMismatch) {
        t.Fatalf("tampered release runtime error = %v", err)
    }
}

func TestLocatorRejectsUnlistedExecutableWhenReleaseManifestExists(t *testing.T) {
    root := t.TempDir()
    name := "engine"
    if runtime.GOOS == "windows" {
        name += ".exe"
    }
    if err := os.WriteFile(filepath.Join(root, name), []byte("fixture"), 0o755); err != nil {
        t.Fatal(err)
    }
    manifest := runtimebundle.Manifest{
        SchemaVersion: runtimebundle.ManifestSchemaVersion,
        Platform: runtime.GOOS + "-" + runtime.GOARCH,
        NFCXVersion: "test",
        Commit: "test-commit",
    }
    if err := runtimebundle.WriteManifest(filepath.Join(root, "manifest.json"), manifest); err != nil {
        t.Fatal(err)
    }
    _, err := runtimebundle.NewLocator(root).Resolve(runtimebundle.Executable{ID: "fixture", FileName: "engine", WindowsFileName: "engine.exe"})
    if !errors.Is(err, runtimebundle.ErrHashMismatch) {
        t.Fatalf("unlisted release executable error = %v", err)
    }
}
'''
write("internal/runtime/locator_test.go", locator_test)

# Regression test: application/runtime source must remain offline-only.
write("internal/security/offline_test.go", r'''package security_test

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
''')

# Security policy documentation.
write("docs/security.md", '''# NFCX local-only security policy\n\nThis fork is hardened for local use. The desktop application does not contain telemetry, online update checks, runtime HTTP clients, or browser-opening links. Build/toolchain scripts may still download pinned third-party source archives; those downloads are build-time only and are verified against repository-pinned SHA-256 values.\n\n## Sensitive local data\n\nTreat the following as credentials or credential-adjacent data:\n\n- `keys.json` and exported key dictionaries;\n- `.bin` / `.mfd` card dumps and `.nfcx.json` sidecars;\n- UID/block-0 backups under the NFCX configuration directory.\n\nApplication-owned sensitive directories are created with mode `0700` and sensitive files with mode `0600` on platforms that expose POSIX permissions. User-selected dump/export parent directories are never chmodded by NFCX. Exported files remain plaintext and should only be stored in trusted local locations.\n\n## External runtime integrity\n\nDevelopment runtimes can be used without a release manifest to preserve local development workflows. Packaged/release runtimes include `manifest.json`; when that manifest is present, every external executable must be listed as executable and its SHA-256 must match before NFCX launches it. A missing entry, invalid manifest, or hash mismatch blocks execution.\n\n## Network boundary\n\nThe desktop runtime is expected to operate without Internet access. CI includes a regression test that rejects runtime source hooks for `net/http`, the former telemetry endpoint, GitHub Releases API update checks, Wails browser-opening hooks, and telemetry/update APIs.\n''')

# README: private/local-only fork and no stale telemetry/update claims.
readme = read("README.md")
readme = replace_exact(readme, 'NFCX is open source and uses a clear, direct GUI so NFC work does not depend on a collection of command-line tools.\n\nWebsite: [nfcx.tools](https://nfcx.tools) · Downloads: [GitHub Releases](https://github.com/BennyThink/NFCX/releases)\n', 'This private fork keeps the MIT-licensed NFCX codebase but is maintained as a local-only hardened build. The desktop runtime is intentionally offline.\n\nRepository: [zhm20/NFCX](https://github.com/zhm20/NFCX)\n', "English fork intro")
readme = sub_once(readme, r'# Download and install\n.*?\n# Quick start', '# Build and run locally\n\nThis fork is intended to be built from source. The normal build still fetches pinned third-party NFC toolchain sources and verifies their recorded SHA-256 values; the resulting desktop runtime does not require Internet access. See [release/build documentation](docs/release.md).\n\n# Quick start', "English build section", re.S)
readme = sub_once(readme, r'# Privacy and anonymous telemetry\n.*?\n# License and third-party software', '# Local-only privacy and security\n\nThis fork removes anonymous telemetry, the telemetry worker, first-run telemetry consent, and GitHub Releases update checks. The desktop runtime contains no intentional network requests.\n\nKeys, card dumps, metadata sidecars, and UID backups are sensitive local data. NFCX restricts app-owned sensitive directories/files where the OS supports it, and warns before exporting plaintext key dictionaries or dump data. See [docs/security.md](docs/security.md).\n\n# License and third-party software', "English privacy section", re.S)
readme = sub_once(readme, r'# Project links\n.*?\n\n# Responsible use', '# Project links\n\n- [Private fork repository](https://github.com/zhm20/NFCX)\n- [Documentation index](docs/README.md)\n- [Local-only security policy](docs/security.md)\n\n# Responsible use', "English project links", re.S)
write("README.md", readme)

zh = read("README.zh-CN.md")
zh = replace_exact(zh, 'NFCX 坚持开源，并用清晰、直接的 GUI 让 NFC 操作不再依赖零散的命令行工具。\n\n官网：[nfcx.tools](https://nfcx.tools) · 下载：[GitHub Releases](https://github.com/BennyThink/NFCX/releases)\n', '本私有 Fork 保留 NFCX 的 MIT 许可代码基础，并按“本地离线、自用安全加固”方向维护；桌面运行时刻意保持离线。\n\n仓库：[zhm20/NFCX](https://github.com/zhm20/NFCX)\n', "Chinese fork intro")
zh = sub_once(zh, r'# 下载和安装\n.*?\n# 快速开始', '# 本地源码构建\n\n本 Fork 以源码构建为主。正常构建流程仍会下载固定版本的第三方 NFC 工具链源码，并使用仓库记录的 SHA-256 校验；构建完成后的桌面运行时不需要访问互联网。详见 [发布/构建文档](docs/release.md)。\n\n# 快速开始', "Chinese build section", re.S)
zh = sub_once(zh, r'# 隐私和匿名遥测\n.*?\n# 许可证与第三方软件', '# 本地隐私与安全策略\n\n本 Fork 已移除匿名遥测、遥测 Worker、首次启动遥测授权和 GitHub Releases 在线更新检查；桌面运行时不包含有意的网络请求。\n\n密钥、卡片 Dump、元数据 sidecar 和 UID 备份都按敏感本地数据处理。操作系统支持时，NFCX 会限制应用自有敏感目录/文件权限，并在导出明文密钥字典或 Dump 前提示风险。详见 [docs/security.md](docs/security.md)。\n\n# 许可证与第三方软件', "Chinese privacy section", re.S)
zh = sub_once(zh, r'# 项目链接\n.*?\n\n\*\*请仅将 NFCX', '# 项目链接\n\n- [私有 Fork 仓库](https://github.com/zhm20/NFCX)\n- [文档索引](docs/README.md)\n- [本地安全策略](docs/security.md)\n\n**请仅将 NFCX', "Chinese project links", re.S)
write("README.zh-CN.md", zh)

# Static site/history links should not redirect users to the upstream repository.
for path in ["index.html", "website/index.html", "website/zh-CN/index.html"]:
    target = ROOT / path
    if target.exists():
        text_value = target.read_text(encoding="utf-8")
        text_value = text_value.replace("https://github.com/BennyThink/NFCX", "https://github.com/zhm20/NFCX")
        target.write_text(text_value, encoding="utf-8")

# Final source-tree assertions before CI.
for removed in [ROOT / "telemetry-worker", ROOT / "internal/telemetry", ROOT / "app/telemetry.go"]:
    if removed.exists():
        raise SystemExit(f"telemetry artifact still exists: {removed}")
for runtime_path in [ROOT / "app", ROOT / "internal", ROOT / "frontend/src"]:
    for path in runtime_path.rglob("*"):
        if not path.is_file() or path.suffix not in {".go", ".ts", ".js"}:
            continue
        text_value = path.read_text(encoding="utf-8")
        for token in ["telemetry.nfcx.tools", "api.github.com/repos/BennyThink/NFCX/releases/latest", "BrowserOpenURL", "TrackTelemetry", "CheckForUpdates"]:
            if token in text_value:
                raise SystemExit(f"runtime source {path} still contains {token}")

print("local-only hardening migration applied")
