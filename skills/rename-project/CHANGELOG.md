# Changelog

## [2.3.1] - 2026-09-07

- 将历史 slash command 升级为通用 Skill，补全自然语言触发、显式输入、共享 Profile 与验收边界。
- 保留业务目的，修正宿主耦合和不安全的隐式动作；迁移案例与实际业务验收分别记录。


All notable changes to this skill are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) · Versioning: [SemVer](https://semver.org/)

## [2.3.0] - 2026-08-24

### Added

- add live project-root migration and host-state continuity workflow
- skip private runtime clones by default and support repeatable --skip-dir exclusions
- verify stable host project IDs, searchable tasks, transcripts, and active process continuity
- add regression tests for generated-directory filtering and failure reports

## [2.2.0] - 2026-08-12

### Added

- add scoped compatibility-path selection
- classify storage and namespace references separately from product text
- protect nested Git roots and write failure reports

## [2.1.0] - 2026-08-12

### Added

- add guarded, compatibility-aware rename execution
- add read-only plans and before/after digests
- stage only files changed by this run and verify GitHub state
