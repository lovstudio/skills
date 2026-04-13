# Changelog

All notable changes to this skill are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) · Versioning: [SemVer](https://semver.org/)

## [0.1.0] - 2026-04-12

### Added

- 重构工作流：备份→全局规划插入点→并行生成→异步插入→清理
- 新增锚点定位机制：插入位置使用上下文文本而非行号，避免偏移问题
- 新增并行生成：通过 Agent 工具并发生成所有图片，总耗时≈单张耗时
- 新增原地插入：图片直接插入原文档，不再仅输出到 images/ 文件夹
- 新增备份安全机制：修改前备份，全部成功后自动清理
- 精简 SKILL.md：从 480 行缩减至 ~120 行，移除冗余说明
- 修复 frontmatter：补充 metadata/license/compatibility 字段

