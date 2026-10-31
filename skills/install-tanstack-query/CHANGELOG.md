# Changelog

## [0.2.2] - 2026-10-31

### Fixed

- CI 自 bf785bd 起每次失败且 0 个 job：validate.yml 调用的 skill-publisher/dev-skills 可复用工作流并不存在。改为在本仓库内运行 lov-skill-creator 的 validate_skill.py（固定到 976fb61）
- README 安装命令改为 npx skills add lov-install-tanstack-query -g -y，插件市场改为 lovstudio/skills 的 dev-tools@lovstudio，移除已归档的 dev-skills 聚合包与 example.com 占位链接

### Changed

- 补齐 validate_skill.py 要求的 Skill 结构：description 精简到 200 字符内，其余触发语移入 Triggers；metadata.tags 改为列表；When to Use 改为 Triggers 并列出非触发条件（项目刻意使用 RTK Query、SWR 或 Apollo，纯命令式副作用，整套应用交给 lov-app-generator，Tauri 命令面与 invoke 适配层交给 lov-optimize-tauri-backend）；新增 references/skill-composition.md；skill.yaml 的 context.profile 补全 schema、source、read、persist

## [0.2.1] - 2026-09-25

### Added

- 合并本地未提交改动到上游 0.2.0 之上
- 本地改动：统一展示名为「TanStack Query 接入」，保持调用 ID 与能力契约。

## [0.2.0] - 2026-08-24

### Added

- add the shared feedback-classification and approval-invalidation gate used by every LovStudio Skill

## 0.1.0 - 2026-07-13

- Extracted into an independent source repository.
- Kept compatible with the `skill-publisher/dev-skills` aggregate bundle.
