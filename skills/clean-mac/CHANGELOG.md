# Changelog

## [0.4.0] - 2026-08-26

### Added

- protect application-managed recording workspaces
- block cleanup and migration of Screen Studio recordings and overlapping protected paths

## [0.3.0] - 2026-08-23

### Added

- rename public Skill identifier to lov-clean-mac
- preserve legacy trigger discovery and existing preference/storage contracts
- add portable npx installation instructions and frontmatter compatibility validation

## 0.2.0

- 增加 `list-staged` 与 `purge-staged`，只按显式 `.cleanup` 路径回收本轮回滚项。
- 移除最终流程对 Finder 批量删除和自动重试的依赖，避免锁定项目引发连续确认弹窗。
- 为多路径 `stage-cleanup` 增加失败回滚与结构化错误状态。
- 增加直接文件系统回收的回归测试，并更新运行手册与安全边界。

## 0.1.0

- 创建目标容量驱动的 macOS 磁盘优化工作流。
- 增加只读盘点、最小计划、归档卷预检、可回滚清理、事务式迁移和真实容量验收 CLI。
- 增加稳定归档结构、保护数据分类、失败恢复与可移植用户配置。
