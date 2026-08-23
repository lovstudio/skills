---
name: lov-ataru-indexing
description: >
  检查并构建本地 Ataru 会话记忆索引，让无界面调用方在检索前拿到 searchable 状态。
  Use when asked to build, rebuild, repair, or check the Ataru memory index.
license: MIT
metadata:
  author: lovstudio
  version: "0.2.0"
  card_standard: lovstudio/skill-card/v1
  tags:
    - ataru
    - indexing
    - local-first
    - memory
  compatibility: "Portable Agent Skills format. Requires Python 3.8+ and a locally installed Ataru binary at 0.41.3 or newer."
  dependencies: []
---

# lov-ataru-indexing — 让本地记忆索引可被检索

把本机 AI 会话历史的 Ataru 索引带到 searchable 状态，并把结果作为一份可判断
的 JSON 报告交回：现在能不能检索、还差多少、这次做了什么。检索本身属于
`lov-ataru-search`。

## Triggers

### Activate when

- “Ataru 索引好像没更新，帮我重建一下。”
- “先确认本地记忆索引是不是可用的。”
- Help me build or repair the local Ataru memory index before searching.

### Do not activate when

- 用户要的是「找出上次怎么解决某个问题」这类检索结果 —— 交给 `lov-ataru-search`，
  它会自己确认索引状态并在未就绪时指回本 Skill。
- 用户在讨论 Ataru 的界面、发布或代码改动 —— 那是产品开发任务，不是索引运维。

## User Profile (cross-session)

`skill.yaml` 声明 `user-profile/v1`。每次运行开始时读取共享的 user、brand、
workspace、preferences 以及本 Skill 的 `skills.lov-ataru-indexing` 命名空间。

本 Skill 唯一值得长期保存的记录是 `records.ataru_bin`：用户机器上那个可用的
Ataru 可执行文件路径。首次解析成功、或用户直接说出该路径时，用
`scripts/profile_store.py record` 写回并报告保存路径；之后把它作为 `--bin` 传入，
省掉每次的候选探测。不要把它硬编码进本源码。完整契约见
[`references/user-profile.md`](references/user-profile.md)。

## Skill Group Composition

见 [`references/skill-composition.md`](references/skill-composition.md)。本源码是
独立 Single Skill，与 `lov-ataru-search` 之间只有制品级交接（索引状态），没有
隐藏的 sibling 依赖。

## Workflow (MANDATORY)

**You MUST follow these steps in order.**

### Step 0: Resolve the binary before anything else

```bash
export SKILL_DIR="$HOME/.claude/skills/lov-ataru-indexing"
python3 "$SKILL_DIR/scripts/ataru_index.py" resolve-bin
```

脚本按「`--bin` 显式参数 → `ATARU_BIN` 环境变量 → PATH → 已安装 App bundle →
从当前目录向上查找的本地 dev build」顺序解析，并对每个候选先跑一次
`--version`。低于 0.41.3 的二进制不认识 `index status`，会把它当成桌面启动参数
**打开一个窗口**并永不返回，所以版本门必须先过。

失败时脚本返回 `ATARU_BIN_NOT_FOUND` 或 `ATARU_BIN_TOO_OLD`，并列出被拒绝的候选
及其版本。把这段原文交给用户，不要自己猜路径。

### Step 1: Read state before deciding to build

```bash
python3 "$SKILL_DIR/scripts/ataru_index.py" status
```

在原始状态之上，报告直接给出三个判断字段：

| 字段 | 含义 |
| --- | --- |
| `needsBuild` | 索引不可检索，必须构建 |
| `isBuilding` | 另一个进程（通常是桌面端）正在构建，不要抢 |
| `progressPercent` | 已处理消息占比，用于告诉用户还要等多久 |

`isBuilding` 为真时不要发起构建。构建锁只在进程内生效，跨进程并发构建虽然靠
「写临时目录再原子替换」兜底，但会白烧一遍全量 CPU。

### Step 2: Bring the index to searchable

```bash
python3 "$SKILL_DIR/scripts/ataru_index.py" ensure --timeout 3600
```

`ensure` 是幂等的：已就绪就直接返回 `already-ready`；有增量就跑
`catch-up-build`；发现别人在构建就先 `waited-for-running-build`。只有用户明确要求
「完全重建」时才加 `--force`（`full-rebuild`），因为它会丢弃现有索引重扫全部会话。

首次全量构建在万级会话的机器上是分钟级操作，默认预算 3600 秒。不要缩短
`--timeout` 去「快速失败」——超时只会留下一个半成品状态。

### Step 3: Report, and only then hand off

把 `actions`、`state`、`totalSessions`、`totalMessages`、`indexSizeBytes`
如实转述给用户。仍然 `state: error` 或 `searchAvailable: false` 时，脚本以退出码 1
结束，报告里的 `error` 字段就是原因，原样交出。

可选的语义索引另算成本，需要时先估：

```bash
python3 "$SKILL_DIR/scripts/ataru_index.py" semantic-preview
```

当前 JSON CLI 的检索只走关键词模式，语义索引只服务桌面端；不要向用户承诺
命令行能拿到 hybrid 结果。

## Dependencies

- Python 3.8+（仅标准库）
- 本机安装的 Ataru 0.41.3 或更新版本

## 通用反馈闭环

用户在 Skill 驱动任务中提出修改意见时，继续当前产物前必须执行：

1. 先判断意见是 `task-specific`（仅本次）还是 `reusable`（可跨任务复用）。
2. `task-specific` 只修改当前任务，不改 Skill。
3. `reusable` 先确定作用域：领域规则先更新对应 canonical Skill；适用于所有 Skill 的规则先更新共享规范。
4. 完成规则更新、版本、lint 与分发核验后，再把修改应用到当前任务。
5. `reusable` 修改会使此前的“确认”“继续”“发吧”失效；完成当前产物修改和回读后必须停下，等待用户下一步指示，不自动进入发布、提交或其他外部写入。
