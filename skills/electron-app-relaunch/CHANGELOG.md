# Changelog

## [0.3.1] - 2026-09-07

### Added

- 统一展示名为「桌面应用重启」，保持调用 ID 与能力契约。

## [0.3.0] - 2026-08-23

### Added

- add Tauri 2 runtime adapters and ownership-aware relaunch paths
- document request_restart versus restart and choose between binary-only and full tauri dev tree replacement
- add Tauri environment, page-load readiness, PID, owner, port, and Cmd+Q verification gates
- fix Agent Skills compatibility frontmatter, portable installation guidance, and validator hygiene

## 0.2.0

- Add development topology selection for self-contained Electron, persistent dev servers, wrappers, and supervisors.
- Add first-versus-warm relaunch timing, environment fingerprint isolation, condition-based waits, and real window readiness gates.
- Add explicit user-quit intent so watchers and helpers do not relaunch after `Cmd+Q`.

## 0.1.0

- Initial local Skill source.
