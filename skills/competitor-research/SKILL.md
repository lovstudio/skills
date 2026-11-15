---
name: lov-competitor-research
description: >
  对点名的产品、公司或开源仓库做竞品调研：差异对比、是否二次开发的血缘溯源、
  含金量与投资视角，结论带可复核证据。Use for competitor analysis or "is A based on B".
license: MIT
compatibility: "Portable Agent Skills format. Needs web search; git and Python 3.8+ for scripts/repo_evidence.py; gh CLI (authenticated) for GitHub facts."
depends_on:
  - lov-branding-consistency
metadata:
  author: lovstudio
  version: "0.1.0"
  card_standard: lovstudio/skill-card/v1
  content_class: authored-prose
  tags:
    - competitor-research
    - competitive-analysis
    - open-source
    - due-diligence
    - provenance
---

# 竞品调研 · Competitor Research

用户点名一组对象（产品、公司、App、网站或开源仓库），这个 Skill 交付一份**结论先行、
每个判断都能回溯到证据**的竞品调研。对开源对象，它用随包脚本从 Git 历史和 GitHub
数据里取证，能回答“A 是不是基于 B 二次开发的”这类单靠阅读 README 答不准的问题。

## Triggers

### Activate when

- “调研 A 和 B 的区别”“做个竞品分析”“A 跟 B 比怎么样”“帮我拆一下这几个竞品”。
- “A 是不是基于 B 二次开发的”“这个项目是不是 fork 的 / 抄的”“查一下它的来源”。
- “这个项目的含金量怎么样”“技术壁垒高吗”“star 是不是刷的”“护城河在哪”。
- 在上面任一轮之后追问“有投资价值吗”“值不值得投”。
- "Compare X and Y", "competitor analysis of these products", "is A a fork of B",
  "how much real engineering is in this repo", "does this project have a moat".

### Do not activate when

- 对象还没点名，要先摸清一个赛道有哪些方案、现状或趋势：用 `deep-research`，拿到候选名单后再回到本 Skill。
- 只核实一句话真假（“X 融了 1 亿是真的吗”）：用 `lov-fact-check`。
- 要为自己的需求选型、出研发或架构方案：用 `lov-dev-research` 或 `lov-solution-architect`；本 Skill 的对比表可作为它们的输入。
- 要测算市场规模 TAM/SAM：交给市场测算类能力，本 Skill 不做规模估算。
- 要买卖股票、代币或资产，或要个性化投资建议：本 Skill 只做业务与技术尽调，不给交易建议。

## 研究模块

每个请求选用下面一到四个模块。用户的追问通常逐级深入，后一个模块复用前面的证据账本，
不重复采集。

| 模块 | 回答的问题 | 默认触发 |
| --- | --- | --- |
| A 差异对比 | 两者定位、用户、实现、覆盖面、协议、规模有何不同 | 任何竞品请求 |
| B 血缘溯源 | 谁派生自谁：fork、拷贝、改写，还是独立实现 | 用户问“是不是基于”“抄的”“fork” |
| C 含金量 | 能力从哪来、自研了什么、热度成色、可持续性 | 用户问“含金量”“壁垒”“刷星”“值不值得用” |
| D 投资视角 | 有无可投实体、商业模式、护城河、价值链位置、风险 | 用户问“投资价值”“值不值得投” |

各模块的检查清单、证据等级、指标口径与报告骨架见
[references/research-playbook.md](references/research-playbook.md)，执行对应模块前读完相关章节。

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

本 Skill 常见的持久记录：`records.default_output`（只在对话里回答，或写成 Markdown 文件）、
`records.default_modules`（例如总是附带 C 模块）、`records.own_product`（用户自己的产品，
对比时作为参照列）。只有用户明确说“以后都……”时才写入。

## Skill Group Composition

Read `references/skill-composition.md` before deciding whether to invoke or
extend any adjacent capability. The record distinguishes optional upstream and
downstream handoffs from embedded Kit modules. Do not silently depend on a
sibling Skill that is not shipped with this source.

## Authorship Integrity

This Skill creates authored prose, so read `references/authorship-integrity.md`
before drafting or revising. Build an authorship ledger from supplied evidence,
audit discourse before sentence polish, preserve counterevidence and unresolved
questions, and never invent firsthand experience, motives, quotations, numbers,
or causal links merely to make the text feel human.

## Workflow (MANDATORY)

**You MUST follow these steps in order.**

### Step 0: Resolve skill root, dependencies, and runtime context

- Use `SKILL_DIR` if the environment provides it; otherwise infer the installed
  skill directory from the current skill context.
- 确认 `scripts/repo_evidence.py` 与 `references/research-playbook.md` 存在。涉及开源对象时
  检查 `git`、`python3`，需要 GitHub 数据时检查 `gh auth status`；缺失时说明哪一项不可用，
  改用网页与 API 公开数据，并在报告里标出缺口。
- Resolve `context.profile`: current request, project context, Skill records,
  shared preferences, shared brand/user profile, then safe defaults.

```bash
export SKILL_DIR="/path/to/lov-competitor-research"
```

### Step 1: 界定对象与问题

- 列出对象及其唯一标识：开源仓库用 `OWNER/REPO`，产品用官网域名，公司用注册名或官网。
  同名对象（例如 PyPI 上的同名包、山寨站点）先排除，再开始采集。
- 选定模块（A–D），写下用户真正要拿到的判断，例如“是不是二次开发”是一个是非题，
  答案必须落在“派生 / 部分借鉴 / 独立实现 / 无法判断”之一。
- 对象超过 5 个或尚未点名时，先交给 `deep-research` 收窄候选，不在这里铺开调研。

### Step 2: 建证据账本并采集

每条事实都进账本：`claim`、`value`、`source`（URL、命令或文件路径）、`retrieved`（绝对日期）、
`status`（verified / partial / unverifiable）。采集失败也要记：保留原始错误，例如
`HTTP 404`、`HTTP 500`、空结果。

开源对象优先跑确定性脚本（命令全部只读，输出 JSON）：

```bash
python3 "$SKILL_DIR/scripts/repo_evidence.py" facts OWNER/REPO OTHER/REPO --star-sample 50
git clone https://github.com/OWNER/REPO.git "$WORK/repo"          # 全量克隆，不加 --filter / --depth
python3 "$SKILL_DIR/scripts/repo_evidence.py" history "$WORK/repo" --alias OldName=NewName
python3 "$SKILL_DIR/scripts/repo_evidence.py" loc "$WORK/repo" --ext py
python3 "$SKILL_DIR/scripts/repo_evidence.py" lineage "$WORK/repo" --source "$WORK/origin" \
  --source-all-history --term author-handle --identifier DistinctiveClassName
```

- `$WORK` 放在会话临时目录，不放进用户项目；结束时说明克隆的位置，以及克隆是否已经删除。
- 脚本只给证据和 `hint`，结论由你读完命中的提交、文件和标识符后再下。
- 产品与公司对象用网页检索和官方资料：官网、文档、定价页、更新日志、应用商店、
  公司公告、监管或工商公开信息、可信媒体。按宿主或用户规定的浏览器能力操作网页，
  需要登录的页面先征得用户同意。

### Step 3: 按模块分析

按 playbook 对应章节执行，关键规则：

- **A 差异对比**：同一维度用同一口径测量两边（例如两边都用 `loc` 计行数）；表格只放
  有来源的值，取不到写“未取得”并说明原因。
- **B 血缘溯源**：同时检查四类证据：平台 fork 关系、首个提交与重写提交、完全相同的文件
  （blob）、源项目特有标识符和作者名在全部历史中的出现。至少找一个反向对照（已知有或
  已知无关系的项目）校准判断。证据等级不足时结论写“无法判断”，不要往有关系或无关系任一边靠。
- **C 含金量**：拆清“能力来自上游”与“自研部分”，用代码占比、测试比、维护集中度、
  停更月份和上游依赖健康度说话；star、fork、issue 比例只是参与深度的启发式指标，
  不能据此断言刷星。
- **D 投资视角**：开头声明不是持牌投资顾问、内容不构成投资建议；先排除代币骗局，
  再看实体、收入、护城河、价值链位置（用有来源的可比融资）、合规与关键人风险，
  最后列出“可能成立的投资逻辑”和“需要向创始人要的数据”。不给买卖、仓位或价格建议。

### Step 4: 写报告

- 第一段先给结论，加粗一句话直接回答用户的问题，后面再跟证据。
- 每个模块一个二级标题；对比放表格，证据放列表，数字带单位与日期。
- 单列“没能核实的项”，写明原因，例如“stargazer 接口返回 404”。
- 外部来源附链接；同一事实各来源说法不一时并列写出，不挑一个当定论。
- 默认在对话中交付；用户要求文件或 `records.default_output` 为文件时，写 Markdown 到
  `workspace` 输出目录或用户指定位置，并报告路径。

### Step 5: 验收

- 账本里的每个数字都能在报告里找到出处，报告里没有账本之外的数字。
- 日期全部是绝对日期；“最近”“今年”这类相对说法已换成具体日期。
- 血缘结论与证据等级一致；含金量结论没有把启发式指标说成事实。
- D 模块包含免责声明，且没有个性化投资建议。
- 列出可选的下游交接（见 composition 记录），只在用户需要时执行。
- 交付时说明报告是只在对话里给出，还是已经写成文件，以及临时克隆的位置和是否已删除。

## 实测约定

- `git clone --filter=blob:none` 的部分克隆会让 `git log -G/-S` 逐个按需下载 blob，
  几百个提交的检索就慢到无法完成；血缘检索一律全量克隆，脚本会拒绝部分或浅克隆（2026-11-15）
- GitHub stargazer 列表对热门仓库可能不可用：REST 返回 404，GraphQL 的 `stargazerCount`
  正常但 `edges` 为空；此时 star 质量记为“无法核实”，不要换口径硬推（2026-11-15）
- GitHub search API 偶发连接断开（报错只有 `EOF`），重试即可；404/401/403 是确定答复，不要重试（2026-11-15）
- PyPI、npm 上的同名包不一定属于该项目，先核对维护者与仓库链接，不能直接拿下载量当安装量（2026-11-15）
- 同一作者常有多个 Git 身份，例如昵称和账号名分开记；不合并时作者集中度会被低估，
  `history --alias` 合并后再算（2026-11-15）
- 用 `uniq -c` 统计每月提交会漏掉零提交月份，停更期要用补全月份的序列来看；脚本已经补全（2026-11-15）
- 被 fork 的源项目之后可能自己演进，只比对源项目当前版本的 blob 会得到 0 重叠；
  怀疑早期 fork 时加 `--source-all-history`（2026-11-15）
- 自定义许可证在 GitHub API 里显示为 `NOASSERTION`，要读仓库里的 LICENSE 原文判断能否商用（2026-11-15）

## Dependencies

- `lov-branding-consistency`：报告属于读者可见文本，交付前按其规则检查语气与信息可见性；
  不改写引文、代码、标识符和数据。
- 运行时：Python 3.8+（仅标准库）、git；GitHub 数据需要已登录的 `gh` CLI。
- 网页检索与浏览能力由宿主提供。
