---
name: lov-feedback-loop
description: >
  把用户对 Agent 的被动情绪与主动点赞、点踩、评分变成可统计的反馈事件，
  按任务、技能、规则、全局 Prompt 的最小作用域迭代，并生成满意度复盘报告。
  Use when the user rates a run, asks for satisfaction stats, or installs the
  feedback loop into another agent.
license: MIT
compatibility: "Portable Agent Skills format. Python 3.8+ standard library only; PyYAML only for validation."
depends_on:
  - lov-branding-consistency
metadata:
  author: LovStudio
  version: "0.3.0"
  card_standard: lovstudio/skill-card/v1
  content_class: deterministic-output
  tags:
    - feedback-loop
    - satisfaction
    - prompt-tuning
    - logging
    - reporting
  internal: true  # plaintext source — never installed; the encrypted public/SKILL.md is what users get
---

# 反馈飞轮 · Feedback Flywheel

四个用户可见的入口：评价、回扫、复盘、接入。
自动链路（情绪感知 → 落账 → 规则迭代）不经过 skill 路由，由根 Prompt 的
反馈与迭代规则加上 `references/protocol.md` 直接驱动；本 Skill 提供主动入口，
同时为自动链路提供协议与脚本。

## Triggers

### Activate when

- 用户对上一轮结果表态：“做得很棒”“太差了”“还是不行”“这次可以”。
- 用户主动 judge：`👍`、`👎`、`❤️`、`🎉`、`🤔`、“这次我给 4 分”、“rate this run”。
- 用户要回扫：“回扫我最近的会话，找出还没闭环的不满”。
- 用户要看统计：“给我一份满意度报告”“看看我最近对 AI 哪里不满意”。
- 用户要接入：“把反馈飞轮装进我的 AI”“install the feedback loop into my agent”。

### Do not activate when

- 用户只是在描述常规业务需求，没有对结果表态；直接执行原任务。
- 用户要长期记住偏好而不是评价本轮结果；交给记忆或 Profile 机制。

## 能力与脚本

| 入口 | 做什么 | 脚本 |
| --- | --- | --- |
| 评价 | 表情、短评、打分归一成事件，回一行收据 | `scripts/feedback_store.py append` |
| 回扫 | 从会话 JSONL 提取用户消息，供判定 | `scripts/scan_session.py` |
| 复盘 | 趋势、未闭环清单、修复时长 | `scripts/report.py` |
| 接入 | 托管块 + 技能链 + 账本，先 dry-run | `scripts/install_feedback_loop.py` |

判定口径、作用域阶梯与状态机见 [references/protocol.md](references/protocol.md)，
字段定义见 [references/store-schema.md](references/store-schema.md)，
宿主路径见 [references/host-adapters.md](references/host-adapters.md)。

## Workflow (MANDATORY)

### Step 0: 定位

- 在 Skill 根目录运行脚本；账本默认 `~/.feedback-loop/`，可用 `FEEDBACK_LOOP_HOME`
  或 `--store` 覆盖（`--store` 写在子命令前后都可以）。
- 缺少脚本或协议时先报出缺失路径，不产出半成品。

### Step 1: 捕获

- 主动评价按下方词表映射；用户明确给出的强度覆盖默认值。
- 被动情绪按协议判定：必须有原话证据，`confidence` 小于 1；强度 1–2 只在形成
  重复模式时落账。
- 回扫历史时先跑 `scripts/scan_session.py --file <会话 JSONL> --last 40`，
  再对提取出的用户消息做判定。

### Step 2: 落账

```bash
python3 scripts/feedback_store.py append \
  --channel explicit --polarity positive --intensity 5 --kind delight \
  --confidence 0.95 --evidence "👍 做得很棒" \
  --host codex --session-id <会话 id> --scope task
```

- 写入前经过去重与凭据遮蔽；重复输入由账本在 10 分钟内自动去重。
- 落账成功后回一行收据，失败时如实报告，不假装已记。

### Step 3: 归因分流

- 先判断 `task-specific` 还是 `reusable`；任务特定只改当前产物。
- 可复用反馈按 `task → skill → reference → root-prompt` 找最窄作用域；
  最小改动清单见协议。

### Step 4: 闭环回填

- 负信号先做最小修复并在原路径回读，再回填 `change-applied` 或 `verified`。
- 只有 `verified` 视为闭环；未完成写 `change-proposed` 并给出复查条件。

```bash
python3 scripts/feedback_store.py update \
  --event-id <事件 id> --status verified \
  --action "<做了什么>" --verification "<怎么回读>"
```

### Step 5: 复盘

```bash
python3 scripts/report.py --since 30d --out <输出目录> --json
```

交付 Markdown 与自包含 HTML，回读 `total`、`unresolved`、`satisfaction` 三个数字。
默认不自动打开浏览器。

### Step 6: 接入其他宿主

```bash
python3 scripts/install_feedback_loop.py --host codex --dry-run
python3 scripts/install_feedback_loop.py --host codex
```

- 只写托管块，块外内容不动；改动前备份。
- 技能目录默认软链到本真源，跨设备分发用 `--copy`。
- 完成后回读：软链解析、托管块计数、块校验和、账本可写。

### Step 7: 自检

```bash
python3 scripts/feedback_store.py verify
python3 scripts/validate_skill.py .
```

## 评价词表

| 用户输入 | polarity | intensity | kind |
| --- | --- | --- | --- |
| `👍`、做得很棒、好耶 | positive | 4 | praise |
| `❤️`、`🎉`、`🔥`、完美、就是这个 | positive | 5 | delight |
| `👌`、没问题、通过 | positive | 3 | approval |
| `🤔`、还行、一般、勉强 | mixed | 3 | lukewarm |
| `👎`、不行、不对 | negative | 4 | dissatisfaction |
| `💩`、`😡`、太差了、气死 | negative | 5 | anger |
| 又错了、还是老问题 | negative | 4 | repeat_complaint |
| 改一下这里：具体内容 | negative | 3 | correction |
| n/5 或“打 n 分” | 1–2 负、3 混合、4–5 正 | max(n,3) | 按极性给 dissatisfaction、lukewarm、praise、delight |

收据用简体中文、不用 emoji、不加感叹，一行说清记录、作用域与下一步。

## User Profile (cross-session)

本 Skill 通过 `skill.yaml` 读取共享 `user-profile/v1`：用户、品牌、工作区、偏好与
`skills.lov-feedback-loop`。用户直接说出的长期偏好，用
`scripts/profile_store.py record --confirm` 写回并报告保存路径；不写入凭据。

## Dependencies

- 运行：Python 3.8+ 标准库。
- 校验：PyYAML（仅 `scripts/validate_skill.py`）。
- 外部服务：无；账本默认只写本地磁盘。
