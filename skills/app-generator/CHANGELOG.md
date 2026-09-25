# Changelog

All notable changes to this skill are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) · Versioning: [SemVer](https://semver.org/)

## [0.5.3] - 2026-09-12

### Added

- UI 规则：所有面向用户的报错文本必须可选中、完整换行并提供一键复制，即使应用全局禁用了文本选择。来自 Lovshrink 视频库探测报错被截断且不可复制的反馈。

## [0.5.2] - 2026-09-07

### Added

- 统一展示名为「应用工坊」，保持调用 ID 与能力契约。

## [0.5.1] - 2026-09-06

### Fixed

- declare required Skill integrations with existing conditional workflow boundaries

## [0.5.0] - 2026-08-25

### Added

- add native macOS Finder Quick Action workflow
- distinguish Finder Quick Actions from Services and audit the Action Extension target, activation rule, presentation, and embedding

## [0.4.0] - 2026-08-24

### Added

- add the shared feedback-classification and approval-invalidation gate used by every LovStudio Skill

## [0.3.2] - 2026-08-14

### Changed

- make `lov-integrate-lovinsp` a mandatory default step for every frontend app
- require idempotent Lovinsp upgrades and supported `code-inspector` migration
- strengthen the audit to validate Vite plugin ordering and legacy dependency removal
- add regression tests for correct, misordered, and legacy Lovinsp configurations

## [0.3.0] - 2026-05-25

### Added

- add web-only app generation path
- add app-type audit profile for auto, web, and tauri checks
- document case-by-case framework selection for Vite, Next.js, PWA, and Tauri
- publish the skill from an independent source repository
- replace author-specific brand paths with portable user configuration

## [0.2.0] - 2026-05-24

### Added

- capture Tauri updater, lovinsp dev, and macOS icon lessons
- audit helper now checks updater pubkey and lovinsp plugin configuration
- brand rules now require padded Tauri icon sources for macOS visual alignment
