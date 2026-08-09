# Changelog

## 0.2.1 — 2026-07-31

- 将 WorkBuddy `sgc-bp.zip` 改为自包含总控包，内置三个子模块。
- 在 Skill frontmatter、`kit.yaml` 和 Connector 元数据中补充 Git 来源标识。
- 增加显式触发词、不应触发条件和子模块缺失错误提示。
- 将 Yoda 案例图片纳入发布包，并阻止 `__pycache__` / `.pyc` 进入产物。
- 强化发布校验，覆盖模块完整性、来源、描述长度、案例链接与生成文件清洁度。

## 0.2.0 — 2026-07-23

- 将单体 `sgc-bp` 升级为可组合的 BP Skill Kit。
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
- 接入 `sgc-any2deck` 生成 PPTX/PDF。
