# NFCX local-only security policy

This fork is hardened for local use. The desktop application does not contain telemetry, online update checks, runtime HTTP clients, or browser-opening links. Build/toolchain scripts may still download pinned third-party source archives; those downloads are build-time only and are verified against repository-pinned SHA-256 values.

## Sensitive local data

Treat the following as credentials or credential-adjacent data:

- `keys.json` and exported key dictionaries;
- `.bin` / `.mfd` card dumps and `.nfcx.json` sidecars;
- UID/block-0 backups under the NFCX configuration directory.

Application-owned sensitive directories are created with mode `0700` and sensitive files with mode `0600` on platforms that expose POSIX permissions. User-selected dump/export parent directories are never chmodded by NFCX. Exported files remain plaintext and should only be stored in trusted local locations.

## External runtime integrity

Development runtimes can be used without a release manifest to preserve local development workflows. Packaged/release runtimes include `manifest.json`; when that manifest is present, every external executable must be listed as executable and its SHA-256 must match before NFCX launches it. A missing entry, invalid manifest, or hash mismatch blocks execution.

## Network boundary

The desktop runtime is expected to operate without Internet access. CI includes a regression test that rejects runtime source hooks for `net/http`, the former telemetry endpoint, GitHub Releases API update checks, Wails browser-opening hooks, and telemetry/update APIs.
