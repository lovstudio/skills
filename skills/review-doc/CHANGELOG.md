# Changelog

All notable changes to this skill are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) · Versioning: [SemVer](https://semver.org/)

## [0.3.1] - 2026-04-16

### Fixed

- Fix comment ID collision and tracked-changes text extraction
- extract: include text inside <w:ins> (tracked changes) — SCHEDULE A etc. now visible
- annotate: auto-detect max comment ID to avoid overwriting pre-existing comments
- annotate: anchor comments inside <w:ins> for tracked-changes paragraphs
- annotate: use CommentsPart._element instead of _blob for reliable persistence

## [0.3.0] - 2026-04-16

### Added

- i18n: bilingual description, triggers, review labels, and annotation tags (EN/ZH)
- Add category: business (商务)
- Expand trigger phrases: annotate document, check contract, 合同审查, 文档批注
- Annotation language now follows document language

## [0.2.0] - 2026-04-15

### Added

- 重命名 review-docx → review-doc，技能名称不再绑定文件格式
- 更新触发词：增加「批阅」「审查合同」等中文触发
- SKILL.md description 重写，突出合同审查核心场景
- README 增加版本 badge

