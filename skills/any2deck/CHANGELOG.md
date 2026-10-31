# Changelog

All notable changes to this skill are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) · Versioning: [SemVer](https://semver.org/)

## [1.1.2] - 2026-10-31

### Added

- 维护备注：补回 2026-08-21 至 2026-09-05 的 5 条经验（此前只在未接入真源的安装副本里），涵盖 `apply-branding.py` 调用目录、大图合成耗时与二维码透明底、`build-batch.ts` 标题识别、讲稿与画面指令分离、满幅风格不叠 logo

### Changed

- `merge-to-pptx.ts` 优先读取 `notes/<stem>.md` 作为演讲者备注，`prompts/` 仅作兜底；只有回退到 `prompts/` 时才拼接基础 prompt（补回安装副本里的改动）

## [1.1.1] - 2026-09-25

### Added

- 合并本地未提交改动到上游 1.1.0 之上
- 本地改动：统一展示名为「PPT 大师」，保持调用 ID 与能力契约。

## [1.1.0] - 2026-08-24

### Added

- add the shared feedback-classification and approval-invalidation gate used by every LovStudio Skill

## [1.0.2] - 2026-05-07

### Fixed

- split detailed workflow into progressive disclosure reference
- move long workflow instructions to references/workflow.md

## [1.0.1] - 2026-05-07

### Fixed

- add release metadata
- add README version badge and changelog entry

