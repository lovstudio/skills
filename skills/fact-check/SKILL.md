---
name: lov-fact-check
description: >
  用真人尽调思路校验用户提出的事实命题：拆解可验证问题、检索一手资料、
  交叉验证证据链，并给出带置信度和不确定边界的结论。
  Trigger when the user asks to fact-check, verify a claim, confirm whether
  something is true, source-check an answer, or mentions "事实校验",
  "帮我确认", "这是真的吗", "verify this", "fact check", "source check",
  "due diligence".
license: MIT
compatibility: >
  Instruction-only skill. Requires web/search access when the claim depends on
  current, external, niche, or source-attributed facts. No local runtime
  dependencies.
metadata:
  author: contributors
  version: "0.1.2"
  tags: fact-check verification research due-diligence source-check
---

# fact-check — 尽调式事实校验

用这个 skill 回答事实真伪问题时，不要直接凭记忆下结论。你要模拟一个认真真人的尽调路径：先澄清命题，拆成可验证子问题，优先查一手资料，再用独立来源交叉验证，最后把证据、推断和不确定性分开写清楚。

## When to Use

- 用户问某个事实是否成立：例如“`Tauri` 程序不支持 GitHub webhook handler 吗？”
- 用户要求“帮我确认”“查证一下”“这是真的吗”“有没有官方依据”。
- 用户给出一段文章、截图、传言、技术判断、商业说法或历史事实，希望判断可信度。
- 用户明确使用 English trigger phrases: `fact check`, `verify this`, `source check`, `is this true`, `due diligence`.

## Core Principle

事实校验不是搜索答案，而是还原“一个谨慎的人会如何确认答案”。

- 先确认问题含义，再确认答案。
- 优先找一手资料：官方文档、源码、标准、法规、公告、论文、原始数据、公司/项目维护者声明。
- 对技术问题，优先官方文档、源码、release notes、issue/PR，再看博客和社区问答。
- 对会随时间变化的问题，必须联网核验，并写明检索日期。
- 把“证据显示”“合理推断”“仍未确认”分开。
- 不要用单一搜索结果做强结论。至少尝试找一个反例或边界条件。

## Workflow (MANDATORY)

**You MUST follow these steps in order:**

### Step 1: Restate the Claim

把用户的问题改写成一个可验证命题，并指出关键歧义。
如果关键歧义会改变检索方向，先用 `AskUserQuestion` 问一个澄清问题；
否则继续执行，不要为了形式而打断用户。

Example:

```text
用户问：“Tauri 程序不支持 GitHub webhook handler 吗？”

可验证命题：
1. Tauri 桌面应用本身是否内置 HTTP server / webhook handler 能力？
2. Tauri 应用能否通过插件、Rust sidecar、本地端口或外部服务接收 GitHub webhook？
3. “不支持”指官方不推荐、没有内置 API，还是技术上完全不能做？
```

### Step 2: Choose Evidence Plan

根据问题类型选择证据路径。

| Claim Type | Primary Sources | Secondary Sources |
|---|---|---|
| 技术能力 / API 支持 | 官方文档、源码、release notes、issue/PR、维护者讨论 | Stack Overflow、博客、示例项目 |
| 产品 / 公司事实 | 官网、公告、SEC/工商资料、官方社媒、新闻稿 | 媒体报道、数据库 |
| 法律 / 政策 / 标准 | 法规原文、政府官网、标准正文 | 律所解读、行业文章 |
| 学术 / 医疗 / 科学 | 论文原文、系统综述、指南、数据集 | 科普文章、新闻报道 |
| 历史 / 人物 / 事件 | 原始档案、采访原文、时间线材料 | 百科、二手转述 |

### Step 3: Search Like Due Diligence

执行检索时必须覆盖这些动作：

1. 查官方来源：项目官网、官方文档、GitHub repo、release notes、官方 FAQ。
2. 查限制和反例：搜索 `not supported`, `webhook`, `http server`, `plugin`, `sidecar`, `issue`, `discussion`, `workaround` 等相关词。
3. 查时间线：确认资料是否过期，尤其技术栈、法规、产品功能。
4. 查独立来源：至少一个非官方来源，用来发现官方文档没有覆盖的实践或争议。
5. 记录证据质量：一手、二手、社区经验、推断。

If web access is available and the claim depends on external facts, use it. Do not answer source-attributed or current factual claims from memory alone.

### Step 4: Evaluate

用下面的判断框架组织结论：

- **Direct evidence**: 一手资料是否直接支持或否定命题？
- **Boundary**: 有无版本、平台、部署方式、权限、安全模型限制？
- **Counterexample**: 是否存在能推翻“完全不支持”的示例或 workaround？
- **Terminology**: 用户用词是否混淆了“没有内置支持”“不推荐”“不能做”？
- **Confidence**: 证据是否足够强？是否还有需要实测或询问维护者的点？

### Step 5: Answer in This Format

默认用中文输出。除非用户要求英文。

```markdown
**结论**
[一句话回答：成立 / 不成立 / 部分成立 / 目前无法确认。]

**更精确的说法**
[把原命题改写成更准确的技术/事实表述。]

**证据链**
1. [来源类型] [来源名称 + 日期/版本，如有]：[它证明了什么]
2. [来源类型] [来源名称 + 日期/版本，如有]：[它证明了什么]
3. [来源类型] [来源名称 + 日期/版本，如有]：[它证明了什么]

**反例或边界**
[列出会改变结论的条件、workaround、版本差异、语义差异。]

**置信度**
[高 / 中 / 低]：[为什么]

**下一步验证**
[如需要：最小复现实验、要查的 issue、要问维护者的问题、要跑的命令。]
```

## Evidence Labels

使用这些标签标注证据质量：

- `[一手]` 官方文档、源码、release notes、维护者直接回复、法规原文、论文原文。
- `[准一手]` 官方示例、官方博客、官方讨论区中维护者回复。
- `[二手]` 媒体、博客、教程、社区问答、百科。
- `[实测]` 本地复现、最小 demo、命令输出。
- `[推断]` 基于证据链的合理判断，但没有直接出处。

## Answer Rules

- 不要把“没搜到”写成“不存在”。只能写“我没有找到直接证据”。
- 不要只给链接列表；必须解释每个来源证明了什么。
- 引用网页时提供链接；不要长段复制原文。
- 技术问题优先给可操作结论：是否能做、推荐怎么做、风险是什么。
- 如果用户问题里有拼写错误，先悄悄修正搜索词，再在结论里只在必要时说明。例如 `tuari` 很可能是 `Tauri`。
- 如果事实依赖日期，写明今天的日期或检索日期。
- 如果无法联网或无法打开关键来源，必须明确说，并把结论降级为“暂定”。

## Example

User:

```text
tuari程序不支持GitHub webhook handler吗？
```

Good answer shape:

```markdown
**结论**
“Tauri 程序不支持 GitHub webhook handler”这个说法不够准确。更准确地说，Tauri 桌面应用通常不内置一个面向公网接收 GitHub webhook 的服务器模型；但它可以通过外部后端、sidecar、本地 HTTP 服务或插件式 Rust 代码参与处理 webhook 流程。

**更精确的说法**
如果你的意思是“GitHub 能直接把 webhook 打到用户本机 Tauri 桌面应用”，这通常不可行也不推荐，因为 webhook 需要公网可达的 HTTP endpoint。如果你的意思是“Tauri 项目里能否写 Rust 逻辑处理 webhook payload”，技术上可以，但通常应由云端服务接收后再通知 Tauri 客户端。

...
```

## Runtime context (shared)

运行前读取本 Skill 包的 `skill.yaml`，由宿主提供 `skill-runtime/v1` 上下文。字段解析顺序为：当前请求、项目上下文、个人 Preferences、品牌 Profile、通用默认值。

- 只使用 Manifest 声明的字段；Profile 保存公开品牌事实，Preferences 保存个人工作偏好。
- `required: true` 字段缺失时，按 Manifest 的问题配置向用户提出一个聚焦问题；用户明确同意后再保存回答。
- 报错提供可复制的 `context_id`、字段路径与来源，诊断内容避开秘密、完整私人路径和原始配置。
