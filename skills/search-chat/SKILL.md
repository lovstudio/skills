---
name: lov-search-chat
description: >
  从本机 Ataru 记忆索引里召回过去的 AI 会话上下文，返回可定位的命中与原文片段。
  Use when asked what was discussed, decided, or fixed in an earlier session.
license: MIT
metadata:
  author: lovstudio
  version: "0.2.0"
  card_standard: lovstudio/skill-card/v1
  tags:
    - ataru
    - search
    - recall
    - local-first
  compatibility: "Portable Agent Skills format. Requires Python 3.8+ and a locally installed Ataru binary at 0.41.3 or newer."
  dependencies: []
---

# lov-search-chat — 从本地记忆里召回上下文

在本机已有的 AI 会话历史里找出与当前问题相关的过去记录，交回两样能直接用的
东西：带稳定标识（Project / Session / Message）的排序命中，以及围绕某个命中的一段
原文。索引的构建与修复属于 `lov-ataru-indexing`。

## Triggers

### Activate when

- “我上次是怎么解决这个报错的？”
- “找出讨论过会话恢复方案的那次记录。”
- Help me recall what was decided about this module in an earlier session.

### Do not activate when

- 用户要的是「把索引重建一下」「索引是不是坏了」 —— 交给 `lov-ataru-indexing`。
- 用户要在当前代码库里找某个符号或文件 —— 用普通的 grep 与文件搜索，那是代码检索
  而不是会话记忆检索。

## User Profile (cross-session)

`skill.yaml` 声明 `user-profile/v1`。每次运行开始时读取共享的 user、brand、
workspace、preferences 以及本 Skill 的 `skills.lov-search-chat` 命名空间。

值得长期保存的记录有两项：`records.ataru_bin`（本机可用的 Ataru 可执行文件路径）与
`records.default_level`（用户偏好的检索粒度）。用户直接说出这类值时，用
`scripts/profile_store.py record` 写回并报告保存路径。检索词、项目 ID 这类一次性
输入不写入 Profile。完整契约见
[`references/user-profile.md`](references/user-profile.md)。

## Skill Group Composition

见 [`references/skill-composition.md`](references/skill-composition.md)。本源码是
独立 Single Skill，与 `lov-ataru-indexing` 之间只有制品级交接（索引状态）。

## Workflow (MANDATORY)

**You MUST follow these steps in order.**

### Step 0: Resolve the binary, then confirm the index

```bash
export SKILL_DIR="$HOME/.claude/skills/lov-search-chat"
python3 "$SKILL_DIR/scripts/ataru_recall.py" index-status
```

解析顺序是 `--bin` → `ATARU_BIN` → PATH → 已安装 App bundle → 从当前目录向上查找的
本地 dev build，每个候选先跑一次 `--version`。低于 0.41.3 的旧版不认识 index 子命令，
会把它当成桌面启动参数**打开一个窗口**并永不返回。

`search` 自己会先确认索引。索引未就绪时它以 `ATARU_INDEX_NOT_READY` 或
`ATARU_INDEX_BUILDING` 失败并指向 `lov-ataru-indexing`，**不会**返回零结果——
「没找到」和「索引没建好」必须是两种可区分的回答。本 Skill 不替用户构建索引。

### Step 1: Choose the level before querying

| level | 一条命中代表 | 什么时候用 |
| --- | --- | --- |
| `turn` | 单条消息 | 默认。要精确定位某句话、某个报错、某个决定 |
| `run` | 一轮用户请求到回答 | 想看一个来回的完整语境 |
| `session` | 整个会话 | 想找「哪次会话在讨论这件事」 |
| `project` | 一个项目 | 想知道这个话题主要发生在哪个项目里 |

```bash
python3 "$SKILL_DIR/scripts/ataru_recall.py" search "会话恢复方案" --level turn --limit 10
```

限定项目时用等号形式，因为项目 ID 本身以短横线开头：

```bash
python3 "$SKILL_DIR/scripts/ataru_recall.py" search "索引没有更新" \
  --level session --project-id=-Users-me-projects-app
```

命中里的 `projectId` / `sessionId` / `messageId` / `lineNumber` 是稳定标识，可以直接
喂给下一步。`snippet` 默认截断到 600 字符，需要完整 CLI 响应时加 `--full`。

命令行检索只走关键词模式：`mode` 与 `requestedMode` 都会是 `keyword`，
`semanticAvailable` 通常为 false。不要向用户承诺命令行能拿到语义或 hybrid 排序，
也不要因为关键词没命中就断言「历史里没有这件事」——换同义词、换 level 再试。

在万级会话的真实语料上，一次 turn 级检索是数十秒量级。不要为了「快速失败」压低
`--timeout`。

### Step 2: Read the original transcript around a hit

排序命中只够定位，不够下判断。拿到候选后，围绕它读一段原文：

```bash
python3 "$SKILL_DIR/scripts/ataru_recall.py" read \
  --project-id=-Users-me-projects-app \
  --session-id=<session uuid> \
  --around=<message uuid or line number> \
  --window 6
```

`--window` 是每侧保留的消息数，`--message-chars` 控制单条正文截断（默认 2000）。
不传 `--around` 时返回会话末尾 `--window` 条。给出的 `--around` 在该会话里找不到时，
脚本报 `ATARU_MESSAGE_NOT_FOUND` 而不是静默返回别的位置。

### Step 3: Answer with citations, not with impressions

回答里必须带得回原处的东西：会话标题、时间戳，以及必要时的 `sessionId`。截断过的
正文要说明是截断的。检索没命中就说没命中，并说明用了哪些词和哪个 level ——
不要用当前上下文的推测去填补历史空白。

## Dependencies

- Python 3.8+（仅标准库）
- 本机安装的 Ataru 0.41.3 或更新版本，且索引已就绪

## 通用反馈闭环

用户在 Skill 驱动任务中提出修改意见时，继续当前产物前必须执行：

1. 先判断意见是 `task-specific`（仅本次）还是 `reusable`（可跨任务复用）。
2. `task-specific` 只修改当前任务，不改 Skill。
3. `reusable` 先确定作用域：领域规则先更新对应 canonical Skill；适用于所有 Skill 的规则先更新共享规范。
4. 完成规则更新、版本、lint 与分发核验后，再把修改应用到当前任务。
5. `reusable` 修改会使此前的“确认”“继续”“发吧”失效；完成当前产物修改和回读后必须停下，等待用户下一步指示，不自动进入发布、提交或其他外部写入。
