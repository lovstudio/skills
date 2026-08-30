---
name: lov-human-writing
description: >
  用作者性账本、篇章审计和 30 项中文表层度量改进稿件，保留真实判断并定位过度解释、
  单线因果和强行收束。Use when users say“去 AI 味”“保留我的判断”或 "humanize this Chinese draft".
license: MIT
compatibility: "Portable Agent Skills format. Python 3.8+ stdlib for surface metrics; semantic authorship and discourse review is instruction-first."
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
depends_on:
  - lov-branding-consistency
metadata:
  author: lovstudio
  version: "0.3.0"
  card_standard: lovstudio/skill-card/v1
  content_class: authored-prose
  tags:
    - chinese-writing
    - humanize
    - ai-detection
    - text-metrics
    - editorial
  dependencies: []
---

# lov-human-writing — 从作者性与篇章开始的中文编辑

先确认文章里哪些判断、取舍和不确定性真正属于作者，再审篇章结构，最后才用
可计算指标处理套话与节奏。产出是一份作者性账本、一份带原文证据的篇章报告、
改好的稿子和改前改后的表层指标对照。

## Triggers

### Activate when

- 「这篇稿子 AI 味太重，帮我改一下」「润色得像人写的」「加点人味」
- 「公众号发之前查一下」，但不承诺通过平台检测，也不输出 AI 概率
- 「量一下这篇有多像 AI」「哪几句最像机器写的」
- "humanize this Chinese draft" / "de-AI my article"
- "help me make this read like a human wrote it"
- "use the metrics to check how AI this draft sounds"

### Do not activate when

- 只要写新稿、不涉及去 AI 味 → 用 `lov-writing-style` 等文风类能力。
- 只要一份检测报告、不要改写 → 仍用本 Skill，但在 Step 3 停下。
- 要模仿某个具体作者的文风 → `lov-style-clone`。
- 英文稿件 → 本引擎的指标（「的」字率、四字格、句读切分）只对中文成立。

## Internal workflows

本仓库只暴露 `lov-human-writing` 一个 Skill。四个阶段是按需读取的内部工作流，
没有独立名称、触发器或安装入口：

- `references/workflows/authorship-ledger.md` — 作者性账本；
- `references/workflows/discourse-audit.md` — 篇章审计；
- `references/workflows/editorial-rewrite.md` — 证据约束改写；
- `references/workflows/surface-audit.md` — 30 项表层度量与复测。

完整任务依次执行四阶段；只审计时跳过改写；只要确定性指标时读取 surface workflow。

## User Profile (cross-session)

Every generated Skill is connected to the shared `user-profile/v1` contract in
`skill.yaml`. Read the shared user, brand, workspace, preferences, and this
Skill's `skills.<skill_id>` namespace at the start of every run. Keep the source
portable: resolved personal values belong in the shared profile, never here.

本 Skill 会持久化两类值：

- `records.default_profile` — 常用的度量档位（`wechat` / `zhuque` /
  `neutral` / `thesis`）。
- `records.baseline_path` — 个人基线 JSON 的路径。**这是本 Skill 最重要的
  持久化项**：默认阈值来自一批公开中文长文，个人基线才是对用户自己文风的
  准确刻画。

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

## 这个 Kit 做什么、不做什么

**做**：先追溯文章命题和结构选择，再检查过度解释、单线因果、反例消失、强行
闭合等篇章问题；最后把 30 项文本统计量与 351 篇真人中文长文的实测分布比较。

**不做**：判断一篇文章是否由 AI 生成。`fail` 的准确含义是「越界密度超过
90% 的真人长文」。向用户汇报时不要把它说成「检测出 AI」或「AI 概率 X%」。
判别侧（对 AI 稿的召回）尚无带标签语料验证，局限记录在
`references/benchmark.md` 第 5 节——被问到准确率时照此回答，不要编数字。

## Workflow (MANDATORY)

**You MUST follow these steps in order.**

### Step 0: Resolve skill root, dependencies, and runtime context

- Use `SKILL_DIR` if the environment provides it.
- Otherwise infer the installed skill directory from the current skill context.
- Verify every required local module, reference, script, and asset before work.
- If a required resource is missing, name its expected relative path and stop
  before producing a partial result.

```bash
export SKILL_DIR="/path/to/lov-human-writing"
```

Resolve `context.profile` on every invocation. The precedence is current request,
project context, Skill-specific profile records, shared preferences, shared
brand/user profile, then safe defaults. A direct user statement about a durable
preference or brand fact should be saved with `scripts/profile_store.py record`
using `--confirm`, followed by a concise saved-path report.

### Step 1: 确定输入、任务边界与档位

输入：文件路径优先；用户直接粘贴则存临时文件再传 `--input`，避免
`--text` 在长稿上撞 shell 参数长度限制。

档位按发布目标选，不要问用户「要哪个 profile」，从场景推断：

| profile | 适用 | 特点 |
|---|---|---|
| `wechat` | 公众号长文（默认） | 适配长段落、第一人称与移动端阅读节奏 |
| `zhuque` | 高强度表层审计 | 收紧结构工整与套话，只作编辑诊断 |
| `neutral` | 通用非虚构 | 不预设口语风格 |
| `thesis` | 学术/正式 | 允许书面语长句，禁 emoji，收紧加粗 |

若 `records.baseline_path` 存在，一并传 `-b`。

### Step 2: 建立作者性账本

完整执行 `references/workflows/authorship-ledger.md`。内部记录：

- 原始问题从哪里来，哪些结论是用户明确给出的；
- 可写成第一人称的真实经历、决定、失败和情绪；
- 作者选择保留、删除或暂不解释的内容；
- 反例、替代解释、利益关系和未解决问题；
- 禁止新增的经历、数字、引语、动机与因果。

输入没有作者判断时，不替作者制造一套“更像人”的立场。用户只要表层报告时，
可走 `surface-only` 管线并明确没有完成作者性验收。

### Step 3: 审计篇章结构

完整执行 `references/workflows/discourse-audit.md` 与
`references/authorship-integrity.md`。逐项给出原文证据，不输出单一 AI 分数：

1. `thesis_provenance`：命题是否可追溯到输入或作者；
2. `causal_compression`：复杂问题是否被压成唯一原因；
3. `counterevidence_survival`：反例是否真正改变论证；
4. `closure_pressure`：结尾是否重复总结、升华或强行行动号召；
5. `reader_inference_budget`：是否把每层意义都替读者解释完；
6. `structural_asymmetry`：章节是否被强行配平；
7. `author_decision_trace`：关键删留与结构选择是否有材料依据。

这些维度是编辑问题，不是身份特征。不要为了“像人”增加无关支线、时间跳跃、
开放结尾或故意不完整；材料本来简单时，清楚和线性可以是正确选择。

### Step 4: 度量表层特征

```bash
python3 "$SKILL_DIR/scripts/measure.py" -i draft.md -p wechat
```

可选参数：`-b baseline.json` 用个人基线覆盖默认区间；`-f json` 取结构化结果；
`--no-locate` 只要指标不要靶点。

### Step 5: 解读并汇报

按结论先行汇报，三件事，不要贴原始表格：

1. 总判定与压力分（例：`fail`，压力分 11，真人基准 p75=7 / p90=9）。
2. 越界的指标，按可改性排序——套话和结构类立刻可改，节奏类要重写句子。
3. 篇章问题与引擎靶点句。二者分别是结构改写和局部改写的直接输入。

用户只要报告就在此停下。要改写则继续。

### Step 6: 结构优先、表层在后的定向改写

完整执行 `references/workflows/editorial-rewrite.md`。先修作者性或篇章问题，再处理表层
越界项。默认局部编辑；只有因果顺序、章节组织或结尾收束确实有证据问题时才重组
相关段落，不做无依据的全文重写。

指标到改法的映射：

| 越界指标 | 改法 |
|---|---|
| `sent_len_cv` / `max_uniform_run` 偏低 | 拆长句、并短句，制造长短交替；不要均匀化 |
| `short_sent_ratio` 偏低 | 把关键判断单独成句 |
| `para_len_cv` / `solo_para_ratio` 偏低 | 转折处、强调处用一句成段 |
| `hard_phrase_per_1k` / `soft_phrase_per_1k` | 删套话，换成具体的事（「随着 AI 发展」→「ChatGPT 发布那周」） |
| `transition_density` 偏高 | 删「首先/其次/此外/综上所述」，靠内容自身接续 |
| `idiom4_per_1k` / `tail_nominal_per_1k` | 删四字格与「体现了/彰显了」式结尾 |
| `neg_parallel_per_1k` | 拆「不是…而是…」排比 |
| `rule_of_three_per_1k` 偏高 | 三项并列改成两项或四项，或直接叙述 |
| `inline_heading_ratio` / `bullet_ratio` / `bold_per_1k` 偏高 | 列表改回段落散文，删装饰性加粗 |
| `heading_per_1k` 偏高 | 合并碎标题 |
| `digit_per_1k` / `concrete_anchor_count` 偏低 | 补具体时间、金额、版本、数量 |
| `first_person_per_1k` 偏低 | 补第一人称经历与判断（`neutral`/`thesis` 档不适用） |
| `hedge_per_1k` 偏高 | 删「可能/或许/一定程度上」，把话说定 |
| `de_ratio` 偏高 | 拆「的」字长定语 |
| `lone_dash_per_1k` | 单破折号 `—` 改中文双破折号 `——` |
| `quote_style_mixed` | 统一到一套引号 |
| `emoji_per_1k` | 删 emoji |

改写时守住三条：

- **不动事实。** 不新增日期、数字、人名、引语。缺具体细节就问用户，不要编。
- **不动立场和专业术语。** 口语化是手段，不是把专业稿改成闲聊。
- **不为凑指标写废话。** 指标是稿子好的副产品，不是目标；把「补第一人称」
  做成硬塞「我觉得」只会更难读。
- **不制造人类噪声。** 不故意加错别字、口头禅、无关支线、矛盾、情绪或开放结尾。
- **不给文章统一收束。** 结尾由材料决定，可以行动、判断、事实、疑问或停在未解处；
  不强制回到价值、未来、自由或“人的意义”。

### Step 7: 双层复测验收

```bash
python3 "$SKILL_DIR/scripts/measure.py" -i draft-v2.md -p wechat \
  --compare draft.md
```

先重跑篇章审计，确认问题被修复且没有丢失作者判断、反例和不确定性；再运行
`--compare` 输出逐项的旧值 → 新值与状态迁移。表层验收标准：目标指标状态改善，
且**没有把别的指标推出界**——去套话时压过头会让 `hedge_per_1k` 或
`short_sent_ratio` 反向越界。压力分没降就说明改写没生效，重来 Step 4，不要
把未改善的结果当成完成。

### Step 8: 交付

- 先调用 `lov-branding-consistency`，但只检查目标媒介、受众、品牌角色与读者可见
  字段；不得借品牌审校改写作者立场、正文事实、引语或已验收的个人声音。没有品牌
  或组件问题时允许零修改。
- 改写稿写到 `./output/`，命名为「原文件名 + `-human-v0.x.md`」。
- 汇报作者性和篇章结构的关键变化、压力分变化、修掉的指标，以及仍然保留的项
  和材料依据。
- 不要声称「已通过 AI 检测」。能说的是指标已回到真人分布区间内。

### Step 9: 建个人基线（强烈建议）

默认阈值来自一批公开中文长文，不是用户本人的文风。有 ≥ 30 篇本人历史稿件时：

```bash
python3 "$SKILL_DIR/scripts/measure.py" --calibrate ~/writing/ --out baseline.json
```

把路径存进 `records.baseline_path`。语料必须是**本人手写**的稿件——混入 AI
生成物或口语转写会污染基线，反而让引擎失效（`references/benchmark.md`
第 1 节记录了一次真实的污染事故与清洗规则）。

## Validate the deliverable

- 作者性账本中的命题、判断和删留决定都有输入依据。
- 篇章报告逐项引用原文证据，没有 AI 概率或平台通过承诺。
- 复测确实跑过，指标改善有 `--compare` 输出支撑，不是凭感觉。
- 事实、立场、术语、反例和有意保留的不确定性未被改动。
- 汇报里没有把分布定位说成 AI 身份判定。
- 输出路径与文件名符合约定。

## Dependencies

`lov-branding-consistency` 只负责最终可见文案的受众与品牌语境。核心编辑与度量使用
Python 3.8+ 标准库，无第三方 Python 依赖。

## References

- `references/benchmark.md` — 阈值与判定标尺的全部来源、复现方法、已知局限。
- `references/authorship-integrity.md` — 作者性账本、七维篇章审计与非虚构边界。
- `references/workflows/` — 四个内部阶段；不作为独立 Skills 分发。
- `references/skill-composition.md` — 与相邻 Skill 的分工与交接。
- `references/user-profile.md` — Profile 契约。
