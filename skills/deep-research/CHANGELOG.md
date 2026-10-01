# Changelog

All notable changes to this skill are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) · Versioning: [SemVer](https://semver.org/)

## [2.6.1] - 2026-10-01

### Changed

- 精简 frontmatter `description` 至 200 字符内，保留原触发语义；完整触发与不触发条件移入正文新增的 `## Triggers`（合并原 “When to Use / NOT Use”）。
- `metadata.tags` 改为列表；`lov-dev-blog` 从 `metadata.dependencies` 移到顶层 `depends_on`，与 `lov-branding-consistency` 并列。
- `skill.yaml` 接入共享 `user-profile/v1` Profile 契约（`read`、`persist` 指向 `skills.deep-research`），原有字段、必填项与提问保持不变，`identity.*` 通过别名桥接 `brand.*`。

### Added

- `references/skill-composition.md`：相邻 Skill、交接边界、重叠决策与组合结论。

## [2.6.0] - 2026-10-01

### Added

- 富媒体成为报告契约：standard 及以上模式必须包含图表（quick ≥1、standard ≥3、deep ≥5、ultradeep ≥8），优先第一手照片、依据引用数字绘制的数据图、结构/流程/时间线示意图与地图。
- 新增 `reference/rich-media.md`：图像来源优先级、照片隐私与 EXIF 处理、版权边界、图注与文件约定、渲染与体积预算。
- `md_to_html.py` 支持图片与图注转换为 `<figure>`，新增 `--embed-images` 生成自包含 HTML；拒绝非 https 的外部协议。
- `validate_report.py` 新增 Figures 检查：零图表或本地图片缺失报错，数量不足、远程图片、缺图注给出警告。

## [2.5.3] - 2026-09-07

### Added

- 统一展示名为「深度研究」，保持调用 ID 与能力契约。

## [2.5.2] - 2026-08-30

### Added

- require an early branching decision guide for comparison, procurement, architecture-choice, and adoption research
- require explicit terminal recommendations and a textual fallback so the decision remains understandable without diagram rendering
- add a strict decision-guide validator and regression tests

## [2.5.1] - 2026-08-30

### Fixed

- render direct HTTP(S) Markdown links as clickable anchors inside report tables and prose
- add regression coverage for shareable repository links and reject non-HTTP URI activation

## [2.5.0] - 2026-08-30

### Added

- add verified open-source solutions landscape workflow
- persist a shareable open_source_solutions.jsonl registry and linked report table
- add strict artifact validation and merge multilingual report validation improvements

## [2.4.0] - 2026-08-24

### Added

- add the shared feedback-classification and approval-invalidation gate used by every LovStudio Skill
