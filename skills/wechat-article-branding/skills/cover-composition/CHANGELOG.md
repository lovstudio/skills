# Changelog

All notable changes to this skill are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) · Versioning: [SemVer](https://semver.org/)

## [0.7.2] - 2026-09-07

### Added

- 统一展示名为「封面合成」，保持调用 ID 与能力契约。

## [0.7.1] - 2026-08-27

### Fixed

- honor cover-specific logo variants
- validate declared white Logo pixels and record the resolved variant in composition receipts

## [0.7.0] - 2026-08-27

### Added

- add verified branded cover composition
- compose wide, square, and optional vertical logo-bearing artifacts with a deterministic receipt

## [0.6.0] - 2026-08-25

### Added

- Default square covers to a bottom-centered publisher Logo while preserving the centered wide composition.
- Crop the dimmed square background before adding a square-specific Logo layer, preventing wide-positioned branding from leaking into the square output.
- Add deterministic square Logo sizing, safe-area defaults, documentation, and validation.
