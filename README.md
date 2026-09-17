# NFCX

<p align="center"><img src="docs/images/nfcx-logo.png" alt="NFCX logo" width="144"></p>

<p align="center"><strong>A cross-platform, open-source, easy-to-use GUI desktop tool for NFC.</strong></p>

<p align="center"><a href="README.md">English</a> | <a href="README.zh-CN.md">简体中文</a></p>

NFCX brings reader discovery, card information, reads, protected writes, raw dumps, key management, and recovery workflows into one desktop application for macOS, Windows, and Linux. It is for MIFARE Classic cards you own or are authorized to test.

This private fork keeps the MIT-licensed NFCX codebase but is maintained as a local-only hardened build. The desktop runtime is intentionally offline.

Repository: [zhm20/NFCX](https://github.com/zhm20/NFCX)

# What NFCX can do

- Discover and connect NFC readers.
- Detect cards and show their UID, ATQA, SAK, and card type.
- Work with MIFARE Classic 1K: authenticate with Key A or Key B, read blocks, edit data, and write changes.
- Save and load compatible raw dumps (`.bin` / `.mfd`) with sidecar metadata; restore with capacity, BCC, access-bit, and per-block read-back checks.
- Scan common keys and manage a local key catalog.
- Run the integrated recovery sequence on a validated PN532 UART reader: common keys, Darkside, Nested, Hardnested, and read verification.
- Use the guarded 4-byte UID/block 0 workflow for supported CUID/Gen2 and Gen1A cards.

# Supported readers

| Reader | Connection / backend | Status | Platforms |
| --- | --- | --- | --- |
| PN532 + FT232RL | Serial, `pn532_uart` via libnfc | **Tested**: discovery, Classic read/write, dump/restore, and key recovery | macOS, Windows, Linux builds |
| Other PN532 UART adapters | Serial, `pn532_uart` via libnfc | **Expected compatible**; not hardware-tested by this project | Depends on adapter driver and serial permissions |
| ACR122U | USB / PC/SC or libnfc | **Unsupported in this release**: NFCX hardware validation and a release profile are not yet available | — |
| ACR1552U | USB / vendor PC/SC driver | **Unsupported in this release**: NFCX hardware validation and a release profile are not yet available | — |
| Other libnfc devices | Varies | **Unsupported** until an explicit NFCX validation profile exists | — |

# Drivers and runtime requirements

NFCX packages its NFC runtime. You do not need to install libnfc, mfoc, mfcuk, or separate command-line NFC tools.

- Linux: your account generally needs read/write serial access (commonly the `dialout` group). For example, run `sudo usermod -aG dialout $USER`, then sign out and back in. You can also run it with `sudo` if you understand the implications.
- macOS: an unsigned release can show a Gatekeeper warning. Use **System Settings → Privacy & Security** to allow it to open when prompted.
- Windows: starting NFCX may require the [FTDI virtual-COM/serial driver](https://ftdichip.com/drivers/).

# Build and run locally

This fork is intended to be built from source. The normal build still fetches pinned third-party NFC toolchain sources and verifies their recorded SHA-256 values; the resulting desktop runtime does not require Internet access. See [release/build documentation](docs/release.md).

# Quick start

1. Connect an NFC reader and launch NFCX.
2. Refresh the reader list or enter the PN532 UART connection string.
3. Place an authorized card on the reader and select **Scan Card**.
4. Review the card information, then use **Key Recovery**, **Read Card**, or **Change UID** as needed.

# Screenshots

## Main window

![NFCX main window](docs/images/main.jpg)

## Key library

![NFCX key library](docs/images/key-lib.jpg)

# Local-only privacy and security

This fork removes anonymous telemetry, the telemetry worker, first-run telemetry consent, and GitHub Releases update checks. The desktop runtime contains no intentional network requests.

Keys, card dumps, metadata sidecars, and UID backups are sensitive local data. NFCX restricts app-owned sensitive directories/files where the OS supports it, and warns before exporting plaintext key dictionaries or dump data. See [docs/security.md](docs/security.md).

# License and third-party software

NFCX source code is released under the [MIT License](LICENSE).
NFCX dynamically links LGPL-3.0-or-later libnfc and redistributes separate GPL-2.0-or-later recovery executables (mfoc, mfcuk, and mfoc-hardnested), plus the BSD-2-Clause `nfc-mfsetuid` utility.
These are independently licensed programs; release packages include their notices, source locations, pinned versions, and NFCX patches.

Read [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) before redistributing NFCX or its runtime.

# Project links

- [Private fork repository](https://github.com/zhm20/NFCX)
- [Documentation index](docs/README.md)
- [Local-only security policy](docs/security.md)

# Responsible use

NFCX is intended for interoperability, research, development, backup, and authorized security testing. 
Use it only with cards and systems you own or have explicit permission to test. 
You are responsible for complying with applicable laws and regulations.

# LICENSE

MIT
