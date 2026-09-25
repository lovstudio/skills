# Changelog

## [0.2.1] - 2026-09-07

### Added

- 统一展示名为「Codeex 插件工坊」，保持调用 ID 与能力契约。

## [0.2.0] - 2026-08-26

### Added

- add a native UI and control-route development loop
- support handleControlRequest scaffolding, validation, and reload-boundary diagnostics
- distinguish renderer/runtime restart from launcher-service reload and require packaged readback
- fix frontmatter compatibility, portable installation, and self-validation hygiene
- document deterministic browser-fixture teardown to avoid profile cleanup races

## 0.1.1

- Required every valid plugin source to appear in the Codeex management page.
- Added authenticated UI install/uninstall and desired/active state round-trip evidence.

## 0.1.0

- Added the audited Codeex runtime plugin manifest and hook contract.
- Added staged source scaffolding and Codeex-owned atomic desired-state lifecycle commands.
- Added isolated install, uninstall, idempotency, failure-preservation, and rollback evidence.
- Documented separation from Codex marketplace plugins, Lovinsp integration, and generic app relaunch.
