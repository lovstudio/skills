---
name: lov-fix-codex-session
description: >
  诊断并修复无法恢复的 Codex 会话：定位悬挂 tool call/output，并在切换模型
  提供商后处理 Model provider not found 的 provider 绑定，恢复交付物与可继续路径。
license: MIT
compatibility: "Portable Agent Skills format. Python 3.8+ standard library only for the
  diagnostic CLIs; reads ~/.codex rollout JSONL and state_*.sqlite, and can sync
  thread provider metadata. No network or external CLI required."
metadata:
  author: skill-publisher
  version: "0.2.0"
  card_standard: lovstudio/skill-card/v1
  content_class: deterministic-output
  tags:
    - codex
    - session-repair
    - rollout
    - provider-sync
    - troubleshooting
    - tool-call
---

# 会话救援 · Session Rescuer

把一条无法继续的 Codex 线程诊断清楚，并给出能继续的产物。它覆盖两种常见
故障：tool call 没有配对的 tool output，以及切换 provider / 中转站后
`Model provider not found`。前者可以从磁盘交付物接手或生成可恢复 rollout
副本；后者只同步 `state_*.sqlite` 的 provider 绑定，不改写 rollout。

## Triggers

### Activate when

- “修复 codex://threads/… 里报错：No tool output found for tool call …”
- “修复 codex://threads/… 里报错：Model provider `custom` not found”
- “切换中转站 / CC Switch 后旧 Codex 线程打不开，需要把 model_provider 统一为当前 provider”
- “这条 Codex 会话继续不了了 / 会话卡死在 systemError / 会话恢复不了”
- “帮我诊断这个 Codex 线程为什么无法继续，怎么救回里面的产物”
- “Fix this stuck Codex session showing 'No tool output found for tool call …'”
- “Sync all Codex thread model_provider values to the current provider name”
- “Diagnose and recover a Codex thread that can no longer be resumed.”

### Do not activate when

- 只是要打开、导航到某个 Codex 会话 —— 交给 `lov-open-codex-session`。
- 只是要检索过去聊过什么 / 上次怎么解决的 —— 交给 `lov-search-chat`。
- 只修改 `config.toml`、不处理 thread 元数据 —— 交给 provider manager / CC Switch；
  本 Skill 处理的是 thread 与配置已经不一致后的恢复。
- 面向任意软件错误的通用定位与修复 —— 交给 `lov-fix-general`；本 Skill 只处理
  Codex 会话持久化状态与 provider 绑定的特定故障。
- 要把修复后的源发布 / 上架 / 上传 —— 交给 `lov-skill-publisher`。

## User Profile (cross-session)

`skill.yaml` 声明 `user-profile/v1`。每次运行开始先读共享的 user、brand、
workspace、preferences 与 `skills.lov-fix-codex-session` 命名空间。线程 id、
rollout 路径、转录内容、秘密或完整私有路径都不写入持久 Profile；涉及会话的
标识只在当前请求内使用。字段解析优先级：当前请求 → 项目上下文 → Skill 记录
→ 共享偏好 → 共享 user/brand Profile → 安全默认值。

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
- Verify every required local module, reference, script, and asset before work.
- If a required resource is missing, name its expected relative path and stop
  before producing a partial result.

When running scripts manually:

```bash
export SKILL_DIR="/path/to/lov-fix-codex-session"
```

`context.profile` 按上述优先级解析。用户直接说出的、希望跨会话保留的值，用
`scripts/profile_store.py record --confirm` 原子写回并报告保存路径；推断值、
秘密、token、cookie 与 key 不入库。

### Step 1: Understand the requested outcome

- Separate internal context from user-visible output.
- Confirm the input, intended audience, expected deliverable, and evidence gaps.
- Record one real user case before calling the Skill complete. The case must show
  the input, the prompt or minimum brief, and the output; do not invent results.
- 先判断故障类型：报错含 `Model provider ... not found` 时，输入是当前
  `config.toml` / `state_*.sqlite`；报错含 `No tool output found` 时，输入是
  **线程 id / codex:// 链接**。输出始终是**一份诊断结论 + 可继续的恢复路径**；
  不要把实现细节作为用户制品。

### Step 1.5: Analyze nearby Skills before implementation

- Inspect related local and installed Skills by routing contract and concrete
  input/output, not by filename alone.
- Record upstream, core, downstream, overlap, and not-composed decisions in
  `references/skill-composition.md`.
- Keep sibling Skills optional and artifact-based. When stages require hard
  coupling for one outcome, create a self-contained Kit instead.
- 本 Skill 是 Codex 会话恢复这一窄领域的核心原子，与通用修复、会话导航、
  会话检索是相邻不重叠关系；见 `references/skill-composition.md`。

### Step 2: Execute the workflow

1. **故障分诊**：错误是 `Model provider ... not found` 时走 `A`；否则按
   `B` 处理悬挂 tool call。
2. **A. 同步 provider 绑定（只读预演）**：
   ```bash
   python3 "$SKILL_DIR/scripts/sync_thread_provider.py" --codex-home "$HOME/.codex" --json
   ```
   确认 `candidate_ids` 只包含真正过期的 provider（默认 `stale-only`，不会
   动 built-in 的 `openai`）。然后退出 Codex Desktop，运行：
   ```bash
   python3 "$SKILL_DIR/scripts/sync_thread_provider.py" --codex-home "$HOME/.codex" --apply
   ```
   脚本会先做 SQLite 一致备份再写 `threads.model_provider`。**不要重写
   `sessions/` 下的 JSONL**：paginated 会话的 `end_byte_offset` 会因此失效。
3. **B. 解析标识**：若错误是悬挂 tool call，从 `codex://threads/<uuid>`、
   线程 id 提取 `thread_id`；若给的是链接，只取 UUID。
4. **B. 定位 rollout**：优先读 `state_5.sqlite` 的 `threads.rollout_path`；拿不到
   就在 `~/.codex/sessions` 下按线程 id 搜索 `rollout-*.jsonl`。
5. **B. 只读诊断**：
   ```bash
   python3 "$SKILL_DIR/scripts/fix_codex_session.py" "$thread_id" --json
   ```
   核对报告中的 `dangling_calls` 与 `last_turn_error`；`poisoned=true` 即为毒点。
6. **恢复交付物**：找出该线程在项目目录里已生成的 Markdown、PDF、图片、代码。
   这些是真正值得抢救的产物，先把它们确认下来并回读。
7. **给出恢复路径**（tool-call 场景二选一，优先第一条）：
   - 在已保存交付物的基础上新开一条干净线程，把收尾工作做完（不要继续旧线程）。
   - 若必须沿用同一线程，运行：
     ```bash
     python3 "$SKILL_DIR/scripts/fix_codex_session.py" "$thread_id" --fix
     ```
     生成 `<rollout>.repaired.jsonl`（不覆盖原文件，宿主未运行线程时才用
     `--write`，且会留 `.bak` 备份）。告知用户：部分宿主需重启或重新加载后
     修复才生效。
8. **验证**：provider 场景回读 `threads.model_provider` 分布并确认无过期 provider；
   tool-call 场景确认修复副本仍是合法 JSONL、`dangling_calls` 已清空、交付物可打开。
   报告具体文件与恢复结论，不要回读被丢弃的私密内容。

### Step 3: Validate the deliverable

- Verify completeness, factual support, user-visible copy, and output paths.
- Report concrete files or results, plus any remaining evidence gaps.
- Validate `skill-card.yaml`, `cases/cases.json`, and `pricing-card.yaml` as the
  standard trust bundle for this Skill.

## Dependencies

- Python 3.8+（仅标准库；`fix_codex_session.py` 与 `sync_thread_provider.py`
  都不需要第三方包）。
- 可读的 Codex 会话目录（默认 `~/.codex/sessions`）；线程 id 用于定位。
- 可读的 `config.toml` 与 `state_*.sqlite`；provider 同步只写 SQLite 索引。
- 宿主若提供 `read_thread` / `list_threads` 等能力，可用于确认线程当前状态。
- 其他 Skill 均为可选手柄，不是运行前提：`lov-open-codex-session`（导航）、
  `lov-fix-general`（通用修复）、`lov-search-chat`（会话检索）。
