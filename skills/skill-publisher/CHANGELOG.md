# Changelog

## [0.7.2] - 2026-08-27

### Fixed

- define `global` / `all` licenses as dynamic access to every currently listed Skill instead of a frozen grant snapshot
- require publication verification to cover dynamic global, explicit ownership, and unentitled Credits paths

## [0.7.1] - 2026-08-27

### Fixed

- require paid Skill Publisher entries to declare and verify either protected encrypted delivery or explicit public-source delivery before publication

## [0.7.0] - 2026-08-24

### Added

- add the shared feedback-classification and approval-invalidation gate used by every LovStudio Skill

## [0.6.0] - 2026-08-24

### Changed

- default channel-less publishing requests to the LovStudio official website
- run all supported adapters only for explicit all-channel or multi-platform requests
- preserve automatic `lov-skill-pricing` as the mandatory pre-publish step
- use the current `LOVSTUDIO_REVALIDATE_SECRET` variable in website revalidation guidance

## [0.5.0] - 2026-08-14

### Added

- support legacy WorkBuddy raw names
- allow external raw_name metadata for updates to existing WorkBuddy listings without changing canonical Skill IDs

## [0.4.1] - 2026-08-14

### Fixed

- target the unified lovstudio/skills catalog
- replace archived General and Dev catalog settings and cache tags

## [0.4.0] - 2026-08-14

### Added

- default every publishing run to evidence-backed automatic pricing
- reuse one lov-skill-pricing Pricing Card across Skill Publisher, WorkBuddy, and SkillPay adapters
- treat explicit user prices as publishing constraints and fix the Skill Publisher reference path

## [0.3.3] - 2026-08-11

### Fixed

- 补齐发布器 compatibility 元数据和 Skills CLI 安装入口

## [0.3.2] - 2026-08-11

### Fixed

- 让 source validator 接受标准 compatibility 元数据

## [0.3.1] - 2026-08-10

### Changed

- 未指定渠道时默认运行全部支持的发布适配器；显式渠道参数仍可收窄发布范围。

## [0.3.0] - 2026-08-03

### Added

- 接入 CodeBuddy WorkBuddy 上架流程
- 使用独立 ZIP、解析成功与审核状态作为发布证据

## [0.2.2] - 2026-08-03

### Added

- 修复 WorkBuddy 子 Skill 的本地资源校验
- 按最近 SKILL.md 解析打包后 references 中的 SKILL_DIR 路径

## [0.2.1] - 2026-08-03

### Added

- 修复 Publisher 自身的 WorkBuddy 自包含打包
- 发布 Publisher 时保留其运行所需的校验与打包脚本

## [0.2.0] - 2026-08-03

### Added

- 统一为 publisher 角色命名
- 同步 Creator 与 Distiller 的发布交接名称

## 0.1.1

- Add Alipay SkillPay as a first-class adapter with explicit package, upload,
  review, and live completion gates.
- Make WorkBuddy Skill Kit modules self-contained by copying shared resources and localizing `$KIT_DIR` references in standalone module packages.
- Preserve the full SemVer suffix when deriving a Connector ZIP name from an output directory such as `v0.2.0`.

## 0.1.0

- Add an independent multi-channel publishing workflow for validated local Skills.
- Support Skill Publisher source, release, catalog, revalidation, and live verification.
- Support external-profile WorkBuddy Connector packaging and import evidence.
- Keep channel metadata and generated artifacts outside canonical Skill source.
- Define a provider adapter contract for future official distribution channels.
