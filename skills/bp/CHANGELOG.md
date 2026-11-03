# Changelog

## [0.3.4] - 2026-11-03

### Fixed

- bp-deck 导出核验新增 PDF 文字层门槛：Chrome/Playwright 打印的 BP 复制或搜索会得到「⼿⼯川」这类部首码位（本机 8 份 BP 与讲义共 3,065 处）。导出后运行 `lov-rich-export` 的 `scripts/fix_pdf_tounicode.py`，`radicals left in text 0` 才算通过；bp-deck 的 `depends_on` 加入 `lov-rich-export`
- 总控视觉门增加「PDF 文字层复制出来是原字：部首码位为 0」

## [0.3.3] - 2026-11-03

### Fixed

- `audit_bp.py`（根目录与 bp-polish 两份）只统计 `## Slide NN — …` 小节：前言里的版本变更说明不再计分；故事节点按页标题判定，正文里「不设融资页」这类提及不再算作覆盖
- Financing delivery 只在融资页内计分，且须写明具体金额；没有融资页记 0 并报「No clear financing ask.」阻断项（一份没有融资页的真实 BP 曾因前言里的「融资 / 资金用途 / 里程碑」得 10/10）
- 补页标题同义词：「为什么是现在」「运营数据」「增长与路线」「产品：…」等；英文词按整词匹配（`sam` 不再命中 `same`，`market` 不再命中 `go-to-market`）
- 审稿 rubric 与报告模板写明：省略的模块（含创始人决定不设的融资页）记 0 分，不得剔除后折算
- 总控视觉门与 bp-polish 视觉 QA 增加「PPTX 可编辑：原生文本、整页图片为 0」

### Added

- bp-deck `scripts/check_pptx_editable.py`：逐页检查原生文本与整页图片，不合格退出 1
- 新增 tests/test_audit_regressions.py、tests/test_pptx_editable.py 与脱敏回归样本 `tests/fixtures/`

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
