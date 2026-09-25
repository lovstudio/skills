# Changelog

All notable changes to this skill are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) · Versioning: [SemVer](https://semver.org/)

## [0.5.1] - 2026-09-07

### Added

- 统一展示名为「研发手记」，保持调用 ID 与能力契约。

## [0.5.0] - 2026-08-26

### Added

- add personal writing style profiles
- resolve, read, and validate configurable writing style profiles before publication

## [0.4.0] - 2026-07-31

### Added

- inventory user-provided screenshots, diagrams, and before/after artifacts
  before drafting
- require narrative placement, descriptive alt text, captions, and responsive
  readability checks for selected inline visuals
- add `scripts/upload_blog_assets.py` for deterministic public asset uploads
- add `--require-inline-image` publishing validation and reject local image
  paths in public posts
- verify public article image URLs, captions, and rendered image count after
  publishing

## [0.3.2] - 2026-05-22

### Changed

- publish direct dev-blog articles by default after dry-run validation
- require an explicit draft/local-only/no-publish request to skip publishing
- document cover generation/upload as part of the default publishing flow

## [0.3.1] - 2026-05-07

### Fixed

- document AskUserQuestion gates for unclear blog publishing

## [0.3.0] - 2026-05-07

### Added

- standardize runtime configuration and skill name
- replace author-local website paths with SKILL_DEV_BLOG_WEB_ROOT
- use canonical skill-publisher CLI install command
