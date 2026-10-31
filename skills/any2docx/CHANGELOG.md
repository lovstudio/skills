# Changelog

All notable changes to this skill are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) · Versioning: [SemVer](https://semver.org/)

## [0.4.2] - 2026-10-31

### Fixed

- 恢复 2026-08-09 去品牌化误改的 `warm-academic` 强调色：`md2docx.py` 主题与未知主题回退色回到 `#CC785C`，与 any2pdf 保持同一调色板（替换前原值见 c01c67a^）
- 新增 tests/test_warm_academic_accent.py

## [0.4.1] - 2026-09-25

### Added

- 合并本地未提交改动到上游 0.4.0 之上
- 本地改动：统一展示名为「Word 大师」，保持调用 ID 与能力契约。

## [0.4.0] - 2026-08-24

### Added

- add the shared feedback-classification and approval-invalidation gate used by every LovStudio Skill

## [0.3.0] - 2026-04-13

### Added

- Add image embedding, auto-refresh TOC, YAML frontmatter stripping, adaptive cover title
- Images: local paths (relative to .md) and remote URLs auto-downloaded and embedded
- TOC: field code + static fallback + updateFields=true for auto-refresh on open
- Frontmatter: YAML front matter block fully stripped from output
- Cover: title font size adapts to length (36pt→22pt) to prevent overflow
- Version: corrected from 1.0.0 to 0.x per repo conventions

