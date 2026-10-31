# Changelog

All notable changes to this skill are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) · Versioning: [SemVer](https://semver.org/)

## [0.3.2] - 2026-10-31

### Fixed

- 恢复 2026-08-09 去品牌化误改的默认归档目录：`find_logo.py` 默认写入 `~/.lovstudio/logo-collection`（本机已有归档所在位置）
- SKILL.md、README 的归档路径同步恢复为替换前原值（3aaa87f^）
- 新增 tests/test_default_output.py，覆盖默认目录与环境变量覆盖

## [0.3.1] - 2026-09-25

### Added

- 合并本地未提交改动到上游 0.3.0 之上
- 本地改动：统一展示名为「Logo 雷达」，保持调用 ID 与能力契约。

## [0.3.0] - 2026-08-24

### Added

- add the shared feedback-classification and approval-invalidation gate used by every LovStudio Skill

## [0.2.0] - 2026-05-07

### Added

- add configurable logo archive output
- standardize install and script invocation examples
- support SKILL_FIND_LOGO_OUTPUT_DIR

