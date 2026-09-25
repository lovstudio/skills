---
name: lov-atom-feature-dev
description: >
  把一个原子功能实现为共享 SDK、CLI、REST API、前端、Profile Preset 与 Agent Skill，并用统一 Dashboard 验证各形态一致性。触发：“完整开发这个 feature”或 “build an atom feature end to end”。
license: MIT
compatibility: "Portable Agent Skills format. Python 3.8+ for the manifest helper; target-project runtimes and test tools are reused in place."
depends_on:
  - lov-branding-consistency
metadata:
  author: LovStudio
  version: "0.2.2"
  card_standard: lovstudio/skill-card/v1
  content_class: deterministic-output
  tags:
    - atom-feature
    - sdk
    - cli
    - restful-api
    - agent-skill
    - profile-preset
    - dashboard
---

# 功能工坊 · Feature Studio

把一个清楚的用户任务收敛成可独立开发、分发、切换和运营的原子 Feature。所有形态
共享一份业务契约与测试向量；前端和 Profile 负责提前确定复杂参数，Agent 只追问仍会
改变交付结果的缺失值。

## Triggers

### Activate when

- “把这个功能完整做成 SDK、CLI、API、前端和 Agent Skill，并加一个调试面板。”
- “以 atom feature 为单位，把 Profile、测试、文档、SEO、登录和支付一起接好。”
- “Build this atom feature end to end with SDK, CLI, API, UI, Agent Skill and dashboard.”

### Do not activate when

- 只需新增一个 CLI、页面、接口或 Agent 对话组件；使用对应单点能力。
- 只需产品架构方案而不实施；使用 solution architecture 能力。
- 只需部署、上架、发布或生产打包；使用现有 release / dev-to-prod 能力。

## Product Contract

- **输入**：目标仓库、一个可命名的用户结果、已有实现与约束；现有项目优先于新脚手架。
- **输出**：原子 Feature manifest、共享核心、适用的分发形态、Profile Preset、前端交互、
  运营配套、可运行的 Companion Dashboard 与跨形态验收证据。
- **完成条件**：至少一个真实测试向量从两个适用形态进入共享核心并得到等价的规范化结果；
  Dashboard 读取真实 manifest、测试与运行证据，不使用手填“已完成”冒充状态。
- **边界**：不强制每个 Feature 都公开全部形态；不引入无价值的登录、支付、SEO 或云部署；
  未获授权不发布、不上传、不改共享权限。

## User Profile

每次运行先读取 `skill.yaml` 与共享 `user-profile/v1`。解析顺序为当前请求、项目上下文、
`skills.lov-atom-feature-dev.records`、共享 preferences、brand/user Profile、安全默认值。
Profile 不是第二套业务逻辑：它只为 Feature Contract 的参数提供可编辑 Preset。

用户直接声明并希望跨任务沿用的默认形态、技术约束或 Preset 规则，通过：

```bash
python3 "$SKILL_DIR/scripts/profile_store.py" record \
  --skill-id lov-atom-feature-dev \
  --path records.default_surfaces \
  --value '["sdk", "cli", "api", "ui", "agent"]' \
  --confirm
```

写回共享 Profile，并报告 canonical 路径。推断值、目标仓库路径和秘密不得持久化。

## Skill Kit Modules

按 `kit.yaml` 加载以下内嵌模块：

- `skills/feature-contract/SKILL.md` — 原子边界、参数、Preset 与验收向量；
- `skills/core-sdk/SKILL.md` — 唯一业务核心和编程语言 SDK；
- `skills/distribution-surfaces/SKILL.md` — CLI、REST API 与 Agent Skill 适配器；
- `skills/profile-experience/SKILL.md` — 前端参数编辑、Preset 与自动化体验；
- `skills/operations/SKILL.md` — 文档、测试、SEO/GEO、用户与支付的适用性闭环；
- `skills/dashboard/SKILL.md` — 多形态切换、运行、对比与证据回读面板。

所有模块通过 `.atom-feature/manifest.json` 与其中引用的制品交接。执行前读取
`references/atom-feature-contract.md`、`references/acceptance-matrix.md` 和
`references/skill-composition.md`。

## Workflow (MANDATORY)

### Step 0: Inspect before shaping

1. 确认目标仓库、适用规则、git 顶层、dirty 状态、实际技术栈和现有运行实例。
2. 搜索已有 SDK、命令、API、UI、Profile、Skill、测试、Auth、支付和文档，避免平行实现。
3. 把目标写成一句“用户提供什么，系统交付什么”；若包含多个独立结果，拆成多个 atom。
4. 选择最小适用 surface 集合。SDK 与共享契约为默认核心，其他形态必须有真实用户或分发价值。

### Step 1: Initialize the source of truth

```bash
python3 "$SKILL_DIR/scripts/atom_feature.py" init \
  --root TARGET_PROJECT --id FEATURE_ID --title "FEATURE_TITLE"
```

如果 `.atom-feature/manifest.json` 已存在，读取并增量维护，不重新初始化覆盖。先执行
`feature-contract`，冻结规范化输入、输出、错误、权限、副作用、Preset schema 和至少一个
真实测试向量。

### Step 2: Build through named pipelines

- 默认 `full`：contract → core SDK → distribution surfaces → profile experience →
  operations → dashboard。
- `surface-first`：已有核心时，从 manifest 和测试向量补 CLI / API / Agent Skill / UI。
- `profile-first`：复杂参数多且追问成本高时，先完成 Preset schema、编辑器和 Agent 解析。
- `audit`：只回读现状和证据，不修改业务实现。

逐模块完成后运行 `atom_feature.py set-status`，只把有真实制品和验证证据的项目标为
`verified`。`implemented`、`verified`、`released` 必须分开。

### Step 3: Enforce one core, many adapters

1. SDK 拥有业务规则；CLI、API、前端与 Agent Skill 只负责输入翻译、权限、传输和呈现。
2. CLI 提供稳定 JSON；API 提供版本化 schema / OpenAPI；Agent Skill 使用同一 typed schema。
3. 前端表单与 Profile Preset 从参数 schema 派生，不维护另一套默认值。
4. Agent 先合并当前请求与 Preset，再询问剩余的结果关键字段；不追问可安全推断或可回读的值。
5. 同一测试向量跨 surface 运行，比较规范化结果与副作用，不比较无关的展示包装。

### Step 4: Close operations and Dashboard

运行 `operations` 判断文档、测试、SEO、GEO、用户系统、支付、分析与支持哪些适用；
不适用项记录理由，不制造空实现。运行 `dashboard` 建立 atom 列表、surface 状态、Preset、
运行参数、结果 diff、日志和验收矩阵，并让每个状态可追溯到文件、命令或运行回读。

Companion Dashboard 随本 Skill 分发，可直接连接任一已初始化项目：

```bash
python3 "$SKILL_DIR/scripts/atom_feature.py" dashboard --root TARGET_PROJECT
```

默认只读并只绑定 loopback。只有用户确实要从面板运行 manifest 已声明的 command array 时
加入 `--allow-run`；只有要保存 `.atom-feature/presets.json` 时加入 `--allow-write`。

### Step 5: Validate the real chain

```bash
python3 "$SKILL_DIR/scripts/atom_feature.py" validate --root TARGET_PROJECT
python3 "$SKILL_DIR/scripts/atom_feature.py" status --root TARGET_PROJECT --format markdown
```

随后运行目标仓库的 lint、typecheck、unit、contract、integration、build 和真实运行验证。
至少验证 golden path、一个参数边界、一个错误路径、Profile 命中与无 Preset fallback。

## Output Contract

结论先写明 atom 是否 `planned`、`implemented`、`verified` 或 `released`，随后给出 manifest、
各 surface 制品、测试命令、Dashboard 路由或入口以及证据缺口。代码构建成功不等于真实
运行通过，本地安装不等于已发布。

## Dependencies

- Python 3.8+ 标准库运行 manifest helper 与本地 Companion Dashboard；Skill 源校验另需 PyYAML。
- 目标项目自己的 SDK、Web、API、测试和构建工具；优先复用既有栈。
- `lov-branding-consistency` 只验收 Dashboard、前端、文档和公开元数据中的受众可见文本。
