# Changelog

All notable changes to this skill are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) · Versioning: [SemVer](https://semver.org/)

## [8.7.0] - 2026-08-24

### Added

- add the shared feedback-classification and approval-invalidation gate used by every LovStudio Skill

## [8.6.0] - 2026-07-25

### Changed

- Move regional and China mirror synchronization into a separately retryable post-CI workflow
- Keep canonical publishing independent from mirror availability or upload duration
- Require post-CI mirror jobs to download immutable assets from the published release tag

## [8.5.0] - 2026-05-08

### Added

- Add hardened Tauri release signing and recovery guidance
- Document Developer ID-only p12 export, notarization secrets, and macOS asset verification
- Add safe release notes output, GitHub API retry polling, draft cleanup, and dirty-worktree safeguards
- Preserve Bun package-manager workflows and add Windows no-bundle zip fallback
