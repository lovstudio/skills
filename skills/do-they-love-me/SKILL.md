---
name: lov-do-they-love-me
description: >
  把两个人的微信私聊做成有证据的恋爱指数分析：量化互动节奏，用本地模型区分工作／情感／生活内容，再产出一张手机竖版信息图。Use when the user says “分析我们的聊天记录”“他／她爱不爱我”，or asks for a chat relationship analysis.
license: MIT
compatibility: >
  Portable Agent Skills format. macOS for the local WeChat query handoff;
  Python 3.9+; Playwright for card rendering and audit; an optional local
  Ollama model for semantic labelling. No network access is required.
depends_on:
  - lov-branding-consistency
metadata:
  author: skill-publisher
  version: "0.2.0"
  card_standard: lovstudio/skill-card/v1
  content_class: microcopy
  tags:
    - wechat
    - relationship
    - analytics
    - infographic
    - privacy
---

# 恋爱指数分析 · Love Index

调用 ID 是 `lov-do-they-love-me`，用的是英文**单数 they**：指一个性别未知或不必指明的人，
所以它同时覆盖 he 和 she。单数 they 的动词形式是 **do**，不是 does——`does they` 是语法错误，
这里不是笔误，后续维护、改名或本地化时不要把它「纠正」成 `does`。
展示名固定为「恋爱指数分析」；ID 与展示名分工不同，不要互相替换。

把一段两个人的真实聊天，做成经得起追问的结论：先量化互动节奏，再做语义分层，
最后交付一张手机竖版信息图。结论必须写清口径、样本与误差，**不许把工作消息当成情感热度**，
也不许把自定义指数说成对当事人情绪的测量。

用户拿到的是三样东西：可复算的中间数据、一张能直接发出去的卡片、以及这套结论的误差范围。

## Triggers

### Activate when

- “分析一下我和某人的聊天记录”“我们聊了两个月，到底算什么关系”。
- “他／她爱不爱我”“帮我做个恋爱指数分析”“看看谁更主动”。
- “把我们的聊天做成一张卡”。
- The user asks to "analyze our chat history", "make a relationship / love index card",
  or "is this person into me, based on the messages".

### Do not activate when

- 只要读取、检索或导出微信记录：交给 `lov-wdb-cli`。
- 已经有结论、只想排版成卡片：交给 `lov-mobile-infographic`；本 Skill 只在没有
  量化与语义结论时从数据开始。
- 要做群聊日报、公众号文章或营销图卡：分别交给日报、文章与图卡类 Skill。
- 没有真实聊天记录、只凭感觉要一个分数：拒绝编造，说明需要数据。

## User Profile (cross-session)

Every generated Skill is connected to the shared `user-profile/v1` contract in
`skill.yaml`. Read the shared user, brand, workspace, preferences, and this
Skill's `skills.<skill_id>` namespace at the start of every run. Keep the source
portable: resolved personal values belong in the shared profile, never here.

When the user directly states a durable preference or brand fact, persist it
through `scripts/profile_store.py` and report the saved profile path. Put
Skill-specific values under `records.<field>`; use `brand.<field>` or
`user.<field>` for shared values. Do not persist inferred secrets or credentials.
See `references/user-profile.md` for the complete contract.

## Skill Group Composition

Read `references/skill-composition.md` before deciding whether to invoke or
extend any adjacent capability. The record distinguishes optional upstream and
downstream handoffs from embedded Kit modules. Do not silently depend on a
sibling Skill that is not shipped with this source.

## Workflow (MANDATORY)

**You MUST follow these steps in order.**

### Step 0: Resolve skill root, dependencies, and runtime context

- Use `SKILL_DIR` if the environment provides it.
- Otherwise infer the installed skill directory from the current skill context.
- Verify `scripts/chat_metrics.py`, `scripts/matrix_dataset.py`, `scripts/export_text.py`,
  `scripts/semantic_label.py`, `scripts/topic_composition.py`, `scripts/card_figures.py`,
  `scripts/verify_figures.py`, and the four references exist before work.
- If a required resource is missing, name its expected relative path and stop
  before producing a partial result.

When running scripts manually:

```bash
export SKILL_DIR="/path/to/lov-do-they-love-me"
```

Resolve `context.profile` on every invocation. The precedence is current request,
project context, Skill-specific profile records, shared preferences, shared
brand/user profile, then safe defaults. A direct user statement about a durable
preference or brand fact should be saved with `scripts/profile_store.py record`
using `--confirm`, followed by a concise saved-path report.

### Step 1: Understand the requested outcome

- 明确对象、时间窗、交付面（自己看 / 发给对方 / 发出去）与语言。
- 读 `references/privacy-and-consent.md`：这是第三方的私人聊天，默认只在本机处理。
- 先定读者与判断：这张卡要回答哪一句可被反驳的判断？写不出判断就回到 Step 3 找证据。

### Step 1.5: Analyze nearby Skills before implementation

- Inspect related local and installed Skills by routing contract and concrete
  input/output, not by filename alone.
- Record upstream, core, downstream, overlap, and not-composed decisions in
  `references/skill-composition.md`.
- Keep sibling Skills optional and artifact-based. When stages require hard
  coupling for one outcome, create a self-contained Kit instead.
- 本 Skill 的既有记录在 `references/skill-composition.md`：上游是 `lov-wdb-cli`，
  下游是 `lov-mobile-infographic`；除非用户改口径，不要重新发明取数或排版。

### Step 2: Execute the workflow

按顺序执行下面五段。每段都以文件为交接物，失败就停在该段并说明缺什么。

**2.1 取数（交给 `lov-wdb-cli`）**

用对方的昵称／备注定位唯一联系人，导出时间窗内的私聊为 JSONL，并记录本机账号与对方账号：

```bash
python3 "$WDB_SKILL/skills/wdb-query/scripts/wdb_cli.py" chats \
  --contact "<昵称或备注>" --from <起> --to <止> --limit 5000 --format jsonl > messages.jsonl
```

先跑 `stats` 看体量与分日分布，再决定窗口。记录 `truncated` 与 `meta.errors`；
不要在卡面或报告里写出账号、库路径、表名。

**2.2 量化**

```bash
python3 "$SKILL_DIR/scripts/chat_metrics.py" \
  --messages messages.jsonl --me <本机账号> --other <对方账号> --out metrics.json
python3 "$SKILL_DIR/scripts/matrix_dataset.py" \
  --messages messages.jsonl --me <本机账号> --other <对方账号> --out matrix.json
```

口径细则见 `references/chat-metrics.md`。`idx` 只是活动度指数，写清权重，别称它为情绪。

**2.3 语义分层（默认全本地）**

```bash
python3 "$SKILL_DIR/scripts/export_text.py" \
  --messages messages.jsonl --me <本机账号> --other <对方账号> --out label_input.jsonl
python3 "$SKILL_DIR/scripts/semantic_label.py" \
  --input label_input.jsonl --out labels.jsonl --model qwen3:8b --batch 20 --context 40
```

- 分类法、判定顺序与失败模式见 `references/semantic-taxonomy.md`。
- 标注是**规则层 + 模型层**两级：没有话题的消息（系统提示、纯应答、纯表情数字、
  纯英文碎片）由脚本按规则判 `other`，其余带上一条上文交给模型。规则层在
  本项目覆盖 10% 的消息且校准集上全对；`--context 0`、`--no-prerules` 只用于对比。
- **必须先校准，再全量标注**：手工标 40–60 条（含工作与情感两类正例、且**不与提示词
  示例重叠**）写成 `gold.json`，先跑
  `semantic_label.py --input label_input.jsonl --eval-gold gold.json --report accuracy.json`，
  把这个配置的 `accuracy.json` 作为结论门槛。
- 门槛：整体一致率 < 80% 不输出占比结论；工作类召回 < 75% 时工作占比要写成下界；
  情感类预测正例不足 5 条时，情感占比只写「个位数百分比」。低于门槛但仍要交付，
  必须在卡面口径行写明「低于门槛、占比仅供参考」。
- 自带默认提示词只用**合成示例**，不含任何真实聊天原句。它在项目自带校准集上的实测是
  一致率 77.1%、工作类召回 0.903：低于 80% 门槛，所以默认输出的占比只作粗分档，
  卡面必须写明「低于门槛、占比仅供参考」。换用使用者自己的校准集后，按新结果重写口径行。
- 复核校准集本身：与分类定义冲突的少数标注按定义修正，并在报告里记下改了什么。
- 想换更强的模型（会把聊天内容发给外部服务商）必须先取得用户明确同意，
  用 `--backend remote --api-key-env <ENV>`，密钥只走环境变量。

```bash
python3 "$SKILL_DIR/scripts/topic_composition.py" \
  --labels labels.jsonl --out composition.json --accuracy accuracy.json \
  --weeks-start <第1周周一> --weeks <周数>
```

**2.4 出图**

```bash
python3 "$SKILL_DIR/scripts/card_figures.py" \
  --matrix matrix.json --composition composition.json --metrics metrics.json \
  --outdir figures --partner-label "<对方昵称>"
```

得到 `figure-matrix.svg`、`figure-composition.svg`、`figure-weekly.svg` 与 `card-data.json`。
版式与注入位置见 `references/card-blueprint.md`。

**2.5 成卡（交给 `lov-mobile-infographic`）**

用该 Skill 的 `scaffold → author → render → audit` 流程，把三张 SVG 注入对应区块，
标题用「恋爱指数分析」，定位标签写「分析对象：<昵称>」，全卡只留一句结论。

### Step 3: Validate the deliverable

- 机器审计：`lov-mobile-infographic` 的 `audit --strict --human-review passed`。
- 几何复核：`python3 "$SKILL_DIR/scripts/verify_figures.py" --card card.html --out verify.json`
  （SVG 标签重叠、溢出、越出画布、被自身 viewBox 裁切）。图上标题与轴标签必须逐个回读确认。
- 口径复核：每个数字都有单位、分母与周期；语义占比必须同时给出模型与一致率；
  「工作不算情感」这条必须在卡面可见。
- 隐私复核：卡面与报告中不出现账号、库路径、表名、真实姓名与联系信息；
  引语做截断并剔除电话／地址／身份证号。
- 最后回读 PNG（原尺寸 + 320px 缩略图）并记录具体发现，再交付。
- Validate `skill-card.yaml`, `cases/cases.json`, and `pricing-card.yaml` as the
  standard trust bundle for this Skill.

## Dependencies

- Python 3.9+ 标准库（`chat_metrics`、`matrix_dataset`、`export_text`、
  `topic_composition`、`card_figures` 无需第三方包）。
- Playwright for Python（`verify_figures`，以及下游卡片渲染与审计）。
- 本地 Ollama（默认语义标注后端，示例模型 `qwen3:8b`）；未安装时必须停下来说明，
  不要静默改用外部 API。
- 上游 `lov-wdb-cli`（取数）与下游 `lov-mobile-infographic`（成卡）都是可选交接，
  不是隐藏依赖：缺少它们时仍可交付 `metrics.json`／`composition.json` 等中间结论。

## Validation

```bash
python3 "$SKILL_DIR/scripts/chat_metrics.py" --help
python3 "$SKILL_DIR/scripts/semantic_label.py" --help
python3 "$SKILL_DIR/scripts/verify_figures.py" --card <card.html>
python3 scripts/validate_skill.py .
```

## Runtime context (shared)

运行前读取本 Skill 包的 `skill.yaml`，由宿主提供 `skill-runtime/v1` 上下文。字段解析顺序为：当前请求、项目上下文、Skill 专属记录、个人 Preferences、品牌/用户 Profile、通用默认值。

- 只使用 Manifest 声明的字段；Profile 保存用户与品牌的共享资料，`skills.lov-do-they-love-me.records` 保存本 Skill 的持久化记录。
- 用户直接说出的长期偏好或品牌事实，通过 `scripts/profile_store.py` 原子写回 Profile，并在结果中报告保存路径。
- `required: true` 字段缺失时，按 Manifest 的问题配置向用户提出一个聚焦问题。
- 报错提供可复制的 `context_id`、字段路径与来源，诊断内容避开秘密、完整私人路径和原始配置。

## 通用反馈闭环

用户在 Skill 驱动任务中提出修改意见时，继续当前产物前必须执行：

1. 先判断意见是 `task-specific`（仅本次）还是 `reusable`（可跨任务复用）。
2. `task-specific` 只修改当前任务，不改 Skill。
3. `reusable` 先确定作用域：领域规则先更新对应 canonical Skill；适用于所有 Skill 的规则先更新共享规范。
4. 完成规则更新、版本、lint 与分发核验后，再把修改应用到当前任务。
5. `reusable` 修改会使此前的“确认”“继续”“发吧”失效；完成当前产物修改和回读后必须停下，等待用户下一步指示，不自动进入发布、提交或其他外部写入。
