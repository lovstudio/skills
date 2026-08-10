# Changelog

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
