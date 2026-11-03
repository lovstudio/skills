# Changelog

All notable changes to this skill are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) · Versioning: [SemVer](https://semver.org/)

## [0.2.1] - 2026-11-03

### Fixed

- `scripts/audit_bp.py` 只统计 `## Slide NN — …` 小节，故事节点按页标题判定，Financing delivery 只在融资页内计分；没有融资页记 0 并报阻断项
- 补「为什么是现在」等页标题同义词，英文词按整词匹配
- rubric 与报告模板写明：省略的模块（含创始人决定不设的融资页）记 0 分，不得剔除后折算
- 视觉 QA 与阻断项增加「PPTX 可编辑：原生文本、整页图片为 0」

## [0.2.0] - 2026-08-24

### Added

- add the shared feedback-classification and approval-invalidation gate used by every LovStudio Skill
