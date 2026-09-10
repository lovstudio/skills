---
name: lov-sync-with-synology
description: Upload local files to a Synology NAS through QuickConnect or DSM HTTPS, verify remote size and MD5, then move the local copy to a reversible trash directory.
license: MIT
metadata:
  author: MarkShawn2020
  version: "1.0.1"
  tags:
    - synology
    - quickconnect
    - file-station
    - upload
    - md5
---

# 群晖同步助手 · Synology Sync

Use this skill when the user wants to move local files to Synology, QuickConnect, DSM File Station, or a Synology Drive target directory, and expects the local source to be cleaned up only after a verified upload.

## Triggers

Activate for requests such as:

- “把本地文件上传到群晖，成功后删本地”
- “用 QuickConnect 上传到 NAS”
- “清理 `~/Music/MP3` 到群晖”
- “move local files to Synology and prune them”
- “upload to DSM File Station and delete the local copy”

### Do not activate when

- The target is Synology C2 Object Storage, S3, or a non-DSM cloud drive.
- The user only wants to browse the NAS without moving local files.
- The user wants to publish, price, or modify this Skill rather than operate it.

## Safety Invariants

1. **Never delete local data before all applicable checks pass.** The CLI verifies remote size and, by default, remote MD5 against the local MD5.
2. **Default deletion mode is `trash`, not `unlink`.** Files are moved under the configured trash directory and can be restored.
3. Use `--delete-mode unlink` only when the user explicitly asks for irreversible deletion.
4. Always run `--dry-run` first for a new source directory.
5. Treat QuickConnect as an access path, not as a storage API. If QuickConnect relay is unavailable, use a reachable `--base-url` (DDNS, VPN, Tailscale, or LAN address).
6. Never put the DSM password in a command line, config file, repository, or chat log. Use macOS Keychain or `SYNO_PASSWORD` for a one-off run.

## Installed CLI

The deterministic CLI is installed at:

```text
~/.local/bin/synology-cli
```

The source implementation and runtime live inside this skill:

```text
~/.agents/skills/lov-sync-with-synology/scripts/synology_cli.py
~/.agents/skills/lov-sync-with-synology/.venv
```

## Standard Workflow

1. Inspect the effective config without printing secrets:

```bash
synology-cli config
```

2. Validate connectivity and File Station API support:

```bash
synology-cli doctor
```

3. Plan the operation without changing the NAS or local files:

```bash
synology-cli run \
  --source ~/Music/MP3 \
  --remote-dir /home/Music/MP3 \
  --dry-run \
  --json
```

4. Run the verified move. The default `trash` mode is reversible:

```bash
synology-cli run \
  --source ~/Music/MP3 \
  --remote-dir /home/Music/MP3 \
  --delete-mode trash \
  --json
```

If the user explicitly requires irreversible local deletion after a successful upload and verification, use `--delete-mode unlink` instead. Do not silently upgrade a request from “清理” to `unlink` without confirming that the local copy is no longer needed.

5. Report the JSON summary and the audit log path. Do not claim success when `ok` is false or `failed` is non-zero.

## Configuration

The default config path is:

```text
~/.config/synology-cli/config.json
```

Key fields:

- `quickconnect_id`, `quickconnect_domain`
- `base_url` as an optional direct fallback
- `username`
- `remote_dir`
- `cert_verify`
- `dsm_version`
- `delete_mode`, `verify_md5`, `recursive`
- `audit_log`

The password is read from macOS Keychain by default:

```bash
security add-generic-password \
  -a "$USER" \
  -s synology-cli \
  -w 'REPLACE_WITH_DSM_PASSWORD' \
  -U
```

`SYNO_PASSWORD` is accepted for one-off automation, but it must never be written to a file or printed.

## Verification

Use the repository-local fake DSM to test the full HTTPS API flow without touching a real NAS:

```bash
~/.agents/skills/lov-sync-with-synology/scripts/test_e2e.sh
```

See `references/operations.md` for the exact safety checks, exit behavior, and recovery procedure.
