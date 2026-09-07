# Changelog

## [8.7.1] - 2026-09-07

- 将历史 slash command 升级为通用 Skill，补全自然语言触发、显式输入、共享 Profile 与验收边界。
- 保留业务目的，修正宿主耦合和不安全的隐式动作；迁移案例与实际业务验收分别记录。


All notable changes to this skill are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) · Versioning: [SemVer](https://semver.org/)

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
