---
name: lov-personal-vocabulary
description: >
  维护一份可跨语音输入法复用的个人词汇表：统一管理、去重、并同步到 Typeless、OpenLess 等 App。Trigger: 帮我维护词汇表、同步词汇、把词汇表填到 OpenLess、manage my personal vocabulary, sync dictation terms across apps.
license: MIT
metadata:
  author: LovStudio / 手工川工作室
  version: "0.2.0"
  card_standard: lovstudio/skill-card/v1
  tags:
    - vocabulary
    - dictation
    - personal-dictionary
    - sync
  compatibility: "Portable Agent Skills format; Python 3.9+ standard library only. App adapters optionally read local JSON or call a vendor API with the user's own credential."
  dependencies:
    - python
---

# lov-personal-vocabulary — 个人词汇表

把散落在各语音输入法里的词条收敛成**一份**属于你的规范词汇表，需要时再按 App 的格式同步回去。不改任何 App 内部行为，只做词条的收集、去重、映射与推送。

## Triggers

### Activate when

- 用户要求维护或整理个人词汇表、术语表、专有名词表，例如“帮我维护词汇表”“整理我的语音输入词库”。
- 用户要求把词汇同步或迁移到某个语音输入法/剪辑工具，例如“把词汇表填到 OpenLess”“同步到 Typeless”。
- 用户给了某款 App 的词汇表来源（文件、API、导出），要求合并去重到统一词库。
- The user asks to manage, dedupe, or sync a personal dictation vocabulary across apps.

### Do not activate when

- 用户只是在正常使用语音输入功能，没有要求维护词库。
- 用户要改某款 App 的语音识别/模型/接口配置本身（交给对应的 App 专项 skill 或人工）。
- 用户要求批量抓取或逆向他人词库、绕过授权；本 skill 只处理用户自己的数据。

## User Profile (cross-session)

本 Kit 通过 `skill.yaml` 连接共享 `user-profile/v1`。每次运行读取共享 user、brand、workspace、preferences 与本 Skill 的 `skills.lov-personal-vocabulary` 命名空间；优先级为当前请求、项目上下文、本 Skill records、共享 preferences、共享 user/brand、保守默认值。

用户直接说出、且明确希望长期沿用的偏好（例如“词汇表放这个目录”“语言用 zh-CN”）才通过 `scripts/profile_store.py record --confirm` 写入 Profile 并报告保存路径。凭据、token、私人路径与推断结论不持久化。完整约定见 `references/user-profile.md`。

## Skill Kit Modules

本仓库是自包含 Skill Kit。Step 0 必须完整加载：

- `$SKILL_DIR/skills/canonical-store/SKILL.md` — `lov-canonical-store`：规范词汇表结构与读写。
- `$SKILL_DIR/skills/app-adapters/SKILL.md` — `lov-app-adapters`：各 App 词条格式与读写映射。
- `$SKILL_DIR/skills/sync-plan/SKILL.md` — `lov-sync-plan`：规范词库与各 App 的差异与同步计划。

`kit.yaml` 定义流水线 `full`（canonical-store → app-adapters → sync-plan）。每个模块必须随本仓库提供，不引用外部 sibling Skill。

## Skill Group Composition

读取 `references/skill-composition.md` 后再决定是否调用或扩展相邻能力。该记录区分可选的上游/下游交接与内嵌 Kit 模块；绝不静默依赖未随本源码提供的 sibling Skill。

## Workflow (MANDATORY)

**你必须按顺序执行以下步骤。**

### Step 0: 解析根目录、依赖与运行时上下文

- 有 `SKILL_DIR` 用它；否则从当前 skill 上下文推断安装目录。
- 开始前校验每个所需本地模块、参考、脚本与资源是否齐全。
- 缺失时点出相对路径并停止，不产出半成品。

手动运行脚本：

```bash
export SKILL_DIR="/path/to/lov-personal-vocabulary"
```

每次调用解析 `context.profile`，优先级见上方。持久化用 `scripts/profile_store.py record --confirm`，随后给出简洁的保存路径报告。

### Step 1: 明确结果

- 区分内部上下文与用户可见产出。
- 确认输入（来源是本地文件、API 还是用户口述）、目标 App、期望产出与证据缺口。
- 记下一个真实用户案例后才算完成；案例必须包含输入、最小 prompt 与输出，不得编造。

### Step 1.5: 分析相邻 Skill

- 按路由契约与具体输入/输出检查相邻本地与已装 Skill，不要只看文件名。
- 在 `references/skill-composition.md` 记录 upstream/core/downstream/overlap/not-composed 决策。
- sibling Skill 保持可选、按产物交接；多阶段强耦合时改为自包含 Kit。

### Step 2: 执行流水线

1. **canonical-store**：建立或读取规范词库 `vocabulary.json`。若来源是新词条，用 `scripts/vocab_cli.py merge` 做按 phrase 去重合并，保留 `enabled`、`hits`、`category` 等已有字段。
2. **app-adapters**：确认目标 App 的读入/写出映射。本地 JSON（如 OpenLess `dictionary.json`）直接读写；走 API 的（如 Typeless `/user/dictionary/list`）用用户自己的凭据、只读探测，绝不打印 token。格式未知的 App（如剪映）先探测再补映射，不得编造。
3. **sync-plan**：用 `scripts/vocab_cli.py diff --app <id> --canonical <path>` 计算差异，产出 `add`（新增）、`skip`（已存在/相同）、`conflict`（同 phrase 不同字段）三类。向用户确认后再执行写入，默认不覆盖对方已有词条。

### Step 3: 校验产物

- 核对完整性、去重正确性、用户可见文案与输出路径。
- 报告具体文件或结果，以及剩余证据缺口。
- 校验 `skill-card.yaml`、`cases/cases.json`、`pricing-card.yaml` 作为标准信任包。

## Deterministic helper

```bash
python3 "$SKILL_DIR/scripts/vocab_cli.py" merge \
  --canonical vocabulary.json \
  --import openless-dictionary.json \
  --from-app openless

python3 "$SKILL_DIR/scripts/vocab_cli.py" diff \
  --app openless \
  --canonical vocabulary.json
```

脚本只做纯文本去重、diff 与格式转换；不访问网络、不写目标 App、不改任何 App 内部数据。

## Dependencies

- Python 3.9+，仅标准库。
- 各 App 的读写按 adapter 选用；无 App 时仅做 canonical 维护，不构成强依赖。

## 通用反馈闭环

用户在 Skill 驱动任务中提出修改意见时，继续当前产物前必须执行：

1. 先判断意见是 `task-specific`（仅本次）还是 `reusable`（可跨任务复用）。
2. `task-specific` 只修改当前任务，不改 Skill。
3. `reusable` 先确定作用域：领域规则先更新对应 canonical Skill；适用于所有 Skill 的规则先更新共享规范。
4. 完成规则更新、版本、lint 与分发核验后，再把修改应用到当前任务。
5. `reusable` 修改会使此前的“确认”“继续”“发吧”失效；完成当前产物修改和回读后必须停下，等待用户下一步指示，不自动进入发布、提交或其他外部写入。
