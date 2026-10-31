# Changelog

## [0.2.3] - 2026-10-31

### Fixed

- 署名恢复为 lovstudio：43873cd 的去品牌化批量替换把 LICENSE 版权方改成 skill-publisher、metadata.author 改成 contributors，按替换前的原值改回
- 0.1.0 条目里被同一次替换改写的 skill-publisher/dev-skills 改回原文 lovstudio/dev-skills

## [0.2.2] - 2026-10-31

### Fixed

- CI 自 43873cd 起每次失败且 0 个 job：validate.yml 调用的 skill-publisher/dev-skills 可复用工作流并不存在。改为在本仓库内运行 lov-skill-creator 的 validate_skill.py（固定到 976fb61）
- README 安装命令改为 npx skills add lov-optimize-tauri-backend -g -y，插件市场改为 lovstudio/skills 的 dev-tools@lovstudio，移除已归档的 dev-skills 聚合包与 example.com 占位链接

### Changed

- 补齐 validate_skill.py 要求的 Skill 结构：description 精简到 200 字符内，其余触发语移入 Triggers；metadata.tags 改为列表；When to Use 改为 Triggers 并列出非触发条件（纯前端 Vite/React HMR，运行时性能交给 lov-app-optimizer，只做查询缓存交给 lov-install-tanstack-query，发版与自动更新交给 lov-app-release、lov-app-delta-updater）；新增 references/skill-composition.md；skill.yaml 的 context.profile 补全 schema、source、read、persist

## [0.2.1] - 2026-09-25

### Added

- 合并本地未提交改动到上游 0.2.0 之上
- 本地改动：统一展示名为「Tauri 后端调优」，保持调用 ID 与能力契约。

## [0.2.0] - 2026-08-24

### Added

- add the shared feedback-classification and approval-invalidation gate used by every LovStudio Skill

## 0.1.0 - 2026-07-13

- Extracted into an independent source repository.
- Kept compatible with the `lovstudio/dev-skills` aggregate bundle.
