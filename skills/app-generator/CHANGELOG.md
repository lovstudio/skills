# Changelog

All notable changes to this skill are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) · Versioning: [SemVer](https://semver.org/)

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
