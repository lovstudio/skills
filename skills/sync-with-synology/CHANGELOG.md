# Changelog

## 1.0.1 - 2026-09-10

- Fix the runtime Skill name and local install path to use the LovStudio `lov-` prefix: `lov-sync-with-synology`.

## 1.0.0 - 2026-09-10

- Added the `synology-cli` CLI.
- Added QuickConnect relay resolution and direct DSM HTTPS fallback.
- Added File Station upload, remote size check, remote MD5 verification, idempotency, and auditable local pruning.
- Added reversible `trash` and explicit `unlink` deletion modes.
- Added macOS Keychain credential support.
- Added local HTTPS fake-DSM end-to-end tests using `~/Music/MP3`.
