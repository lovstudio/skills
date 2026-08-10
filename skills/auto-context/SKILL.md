---
name: lov-auto-context
category: Dev Tools
tagline: "Context hygiene operator. Evaluates, writes memory, edits CLAUDE.md, suggests /fork or /compact."
description: >
  Manual or hook-triggered context operator. Evaluates the current session for
  pollution (long conversations, topic drift, stale noise), AND takes concrete
  context-shaping actions: writing project memory, updating global or project
  CLAUDE.md (with diff + confirm), and recommending harness commands like
  /fork, /compact, /btw. Covers the full surface of context-affecting
  operations Claude can reach — direct file edits are auto-executed or
  confirmed based on sensitivity; harness-only commands (/fork etc.) are
  surfaced as one-click suggestions.
license: MIT
compatibility: >
  Claude Code-oriented instruction skill. Agent home must resolve from
  `SKILL_AUTO_CONTEXT_AGENT_HOME`, the shared Skill Publisher skills profile, or
  a one-time user answer; do not assume a fixed runtime directory.
metadata:
  author: contributors
  version: "0.3.1"
  tags: context memory claude-code
---

# AutoContext: Context Operator

Not just a health check — a full operator over everything that shapes
context. Three layers by action sensitivity:

| Layer | Examples | Behavior |
|-------|----------|----------|
| **Auto-execute** | write project memory, update `MEMORY.md` index | Do it, report path |
| **Confirm-first** | edit global agent instructions, edit project `CLAUDE.md`, overwrite/delete existing memory | Show diff, wait for "yes" |
| **Suggest-only** | `/fork`, `/compact`, `/btw`, new session | Print the exact command to paste |

The harness owns `/fork` and `/compact`; this skill cannot invoke them. But
it can do everything else and will.

## Auto Mode (via Plugin Hook)

When the skill-publisher plugin is enabled, a `UserPromptSubmit` hook monitors
transcript size. Above threshold (40+ entries or 150KB+), it injects a
lightweight `<auto-context>` reminder.

**When you see `<auto-context>`:**

| Context State | Action |
|---------------|--------|
| Mostly relevant | Continue, say nothing |
| Some stale noise | Mentally deprioritize, proceed |
| Mostly irrelevant | Suggest `/fork` or `/btw` with exact command |
| Near capacity | Suggest `/compact` or `/fork` with exact command |

Rules:
- 1 sentence max unless acting.
- If context is fine, say nothing.
- Never auto-fork/auto-compact (can't anyway — harness-only).
- Don't mention "AutoContext" unless asked.

## Manual Mode (`/lov-auto-context [args]`)

Two call shapes:

### A. Bare call — health report + opportunistic memory write

```
/lov-auto-context
```

1. **Measure** — estimate turns, tool calls, distinct topics
2. **Assess** — healthy / getting noisy / polluted / critical
3. **Scan recent turns for unpersisted feedback/preferences** —
   if the user stated a rule or preference earlier in the session that
   should persist to future conversations (typical trigger phrases:
   "从今以后", "以后都", "所有 X 应该 Y", "别再", "记住"), and no
   memory was written, auto-execute: write the memory file + update
   `MEMORY.md`. Report the path.
4. **Recommend** harness actions if needed (`/fork`, `/compact`, `/btw`)
   with the exact command to paste.

Keep to 3-5 lines unless taking confirm-first actions.

### B. With arguments — targeted context operation

```
/lov-auto-context <free-form instruction>
```

Parse the instruction and route to the right action class:

| Instruction pattern | Action | Sensitivity |
|---|---|---|
| "记到全局 / write to global / 加到全局指令" | edit the configured global instructions file | **Confirm-first** |
| "记到项目 / 加到项目 CLAUDE.md" | edit project `CLAUDE.md` | **Confirm-first** |
| "记住 X / 记到 memory" | write project memory | Auto-execute |
| "忘掉 X / forget X" | remove relevant memory file + index entry | **Confirm-first** |
| "该分叉了吗 / should I fork" | evaluate + suggest command | Suggest-only |
| "压缩一下 / compact" | suggest `/compact` with exact syntax | Suggest-only |

## Action: Write Project Memory (auto-execute)

Directory: `<resolved-agent-home>/projects/<project-slug>/memory/`.
Resolve `<resolved-agent-home>` from the User Configuration section before
writing. The memory directory should already exist; do not create a new
runtime layout silently.

Procedure:
1. Pick filename: `<type>_<topic>.md` (e.g. `feedback_output_paths.md`).
2. Write with the required frontmatter (`name`, `description`, `type`).
3. For `feedback` / `project` types, include `**Why:**` and
   `**How to apply:**` lines.
4. Update `MEMORY.md` with one-line pointer under 150 chars.
5. Report the absolute + relative path.

## Action: Edit Global CLAUDE.md (confirm-first)

Target: `<resolved-agent-home>/CLAUDE.md`.

Procedure:
1. Read the file.
2. Locate the best section for the addition (match existing heading like
   "输出规范", "网络 / 代理", "Debugging Discipline"; or create a new
   section if none fits).
3. **Show the proposed diff** as a fenced block with `-`/`+` lines.
4. Ask: "执行这个修改？(yes/no)"
5. On "yes" → apply via `Edit`. On anything else → abort, optionally
   offer to save as project memory instead.

Never skip the diff step. `CLAUDE.md` is user-authored authoritative
config; silent edits erode trust.

## Action: Edit Project CLAUDE.md (confirm-first)

Same flow as global, but target is `<cwd>/CLAUDE.md` (walk up if not at
root). Same diff-then-confirm requirement.

## Action: Suggest Harness Commands (suggest-only)

Produce the exact string the user should paste, not a description:

```
context polluted — paste this to fork:
/fork
```

or

```
approaching capacity — compact first, then continue:
/compact
```

Do not wrap in explanations. The command is the deliverable.

## What this skill cannot do (be honest about it)

- Invoke `/fork`, `/compact`, `/btw`, `/clear`, new session — harness-only.
- Edit another agent's transcript.
- Auto-install hooks — use `/update-config` for that.

If the user asks for one of these, say so and give them the command to
paste.

## Output convention

Every action that writes a file must echo its absolute + relative path
(per project-wide output-paths rule). Applies to memory files, CLAUDE.md
edits (show final path), and any derived artifacts.

## User Configuration

Resolve agent paths in this order:

1. `SKILL_AUTO_CONTEXT_AGENT_HOME`.
2. Shared profile `${SKILL_PROFILE_PATH:-$HOME/.skill-publisher/skills/profile.json}`
   keys: `agent.home`, `claude.home`, or `runtime.agent_home`.
3. Ask the user once for the agent home directory and use that value for the
   current operation.

For alternate runtimes, set `SKILL_AUTO_CONTEXT_AGENT_HOME` explicitly or
add the relevant profile key.

## Runtime context (shared)

运行前读取本 Skill 包的 `skill.yaml`，由宿主提供 `skill-runtime/v1` 上下文。字段解析顺序为：当前请求、项目上下文、个人 Preferences、品牌 Profile、通用默认值。

- 只使用 Manifest 声明的字段；Profile 保存公开品牌事实，Preferences 保存个人工作偏好。
- `required: true` 字段缺失时，按 Manifest 的问题配置向用户提出一个聚焦问题；用户明确同意后再保存回答。
- 报错提供可复制的 `context_id`、字段路径与来源，诊断内容避开秘密、完整私人路径和原始配置。
