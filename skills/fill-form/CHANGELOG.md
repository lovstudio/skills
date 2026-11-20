# Changelog

All notable changes to this skill are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) · Versioning: [SemVer](https://semver.org/)

## [1.2.2] - 2026-11-20

### Fixed

- README 的安装命令改为 `npx lovstudio skills add fill-form -g -y`：不带斜杠的名字会被 `npx skills add` 当作 git 源，报 repository does not exist，装不上。

## [1.2.1] - 2026-09-25

### Added

- 合并本地未提交改动到上游 1.2.0 之上
- 本地改动：统一展示名为「表单小助手」，保持调用 ID 与能力契约。

## [1.2.0] - 2026-08-24

### Added

- add the shared feedback-classification and approval-invalidation gate used by every LovStudio Skill

## [1.1.2] - 2026-05-07

### Fixed

- remove system pip flag from script docs
- use python3 -m pip install python-docx in dependency examples

## [1.1.1] - 2026-05-07

### Fixed

- add release metadata
- add README version badge and changelog entry

