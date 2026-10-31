# Changelog

## [0.3.2] - 2026-10-31

### Fixed

- 恢复 2026-08-09 去品牌化误改的默认 profile：`init_bp.py`（含 bp-outline 副本）默认读取 `~/.lovstudio/skills/profile.json`，各 user-config.md 的路径同步恢复（替换前原值见 02044aa^）
- WorkBuddy 打包：`git_url` 在脚本、connector-meta.json、kit.yaml 与 SUBMISSION.md 恢复为 `https://github.com/lovstudio/bp-skill`；生成包 `author` 按 BRAND-08 写作 `Lovstudio.AI`；图标填充色恢复 `#D97757`
- 包校验的私有路径检查恢复为原值 `/Users/mark`（替换后检查的是永不出现的 `${SKILL_USER_ROOT}`）
- 新增 tests/test_sanitizer_regressions.py

## [0.3.1] - 2026-09-25

### Added

- 合并本地未提交改动到上游 0.3.0 之上
- 本地改动：统一展示名为「BP 精修」，保持调用 ID 与能力契约。
- 本地改动：统一展示名称为「BP 审校」，保留原有调用 ID 与能力边界。

## [0.3.0] - 2026-08-24

### Added

- add the shared feedback-classification and approval-invalidation gate used by every LovStudio Skill

## 0.2.1 — 2026-07-31

- 将 WorkBuddy `lov-bp.zip` 改为自包含总控包，内置三个子模块。
- 在 Skill frontmatter、`kit.yaml` 和 Connector 元数据中补充 Git 来源标识。
- 增加显式触发词、不应触发条件和子模块缺失错误提示。
- 将 Yoda 案例图片纳入发布包，并阻止 `__pycache__` / `.pyc` 进入产物。
- 强化发布校验，覆盖模块完整性、来源、描述长度、案例链接与生成文件清洁度。

## 0.2.0 — 2026-07-23

- 将单体 `lov-bp` 升级为可组合的 BP Skill Kit。
- 新增可独立安装的 `bp-outline`、`bp-deck`、`bp-polish` 三个子 Skill。
- 总控入口根据用户意图选择一个或多个模块，不再强制跑完整流程。
- 建立共享工作区、证据门、视觉门和最多三轮的回退修正机制。
- 保留 v0.1.0 的工作区初始化与审稿脚本入口。
- 新增腾讯 WorkBuddy `skill-only Connector` 发行包、独立 Skill ZIP 和自动校验。

## 0.1.0 — 2026-07-23

- 首次公开发布。
- 建立证据账本、投资叙事、12–15 页结构与专业图表规范。
- 提供 BP 工作区初始化和确定性审稿脚本。
- 收录 Yoda 种子轮 BP 真实迭代案例与质量报告。
- 接入 `lov-any2deck` 生成 PPTX/PDF。
