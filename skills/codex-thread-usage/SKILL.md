---
name: lov-codex-thread-usage
description: >
  从本地 Codex deeplink 或 thread UUID 核算整个线程与最新快照的 token usage；适用于“查这个 Codex 任务消耗”“统计 thread tokens”和 inspect Codex thread usage。
license: MIT
metadata:
  author: lovstudio-contributors
  version: "0.1.1"
  card_standard: lovstudio/skill-card/v1
  tags:
    - codex
    - token-usage
    - deeplink
    - local-diagnostics
  compatibility: "Python 3.9+; local Codex state_5.sqlite and rollout JSONL."
  dependencies: []
---

# Codex 用量账本 · Codex Usage Ledger

把一个本地 Codex deeplink 解析成 thread ID，以只读方式检查 SQLite 快照和
rollout JSONL，给出整个线程、最新计数段和 token 类型的可核验统计。

## Triggers

### Activate when

- 用户说“查这个 Codex 任务消耗”“这个 deeplink 用了多少 token”或“统计 thread tokens”。
- The user asks to “inspect Codex thread usage” or “calculate tokens for this Codex deeplink”.
- 输入是 `codex://threads/<uuid>` 或 Codex thread UUID，并要求 token 明细或统计口径。

### Do not activate when

- 用户询问账户订阅额度、五小时/周限额或 reset credits；这些是账户 rate limit，不是单线程 token 统计。
- 用户要求估算 API 账单金额；本 Skill 不内置会变化的模型价格，也不把 cached token 当作免费 token。
- 用户只想打开或导航到 deeplink；应使用宿主的任务导航能力。

## User Profile (cross-session)

Read `skill.yaml` on every run and resolve the shared `user-profile/v1` context.
Current request and explicit flags take precedence over Skill records and shared
preferences. Persist only direct durable user statements through
`scripts/profile_store.py`; never persist thread IDs, transcripts, credentials,
or inferred private paths.

## Skill Group Composition

Read `references/skill-composition.md` before composing adjacent capabilities.
This Skill owns the local deeplink-to-usage result and has no required sibling
Skill dependency.

## Workflow (MANDATORY)

### Step 0: Resolve runtime

1. Resolve `SKILL_DIR` from the active Skill context.
2. Read `skill.yaml`, `references/token-semantics.md`, and
   `references/skill-composition.md` completely.
3. Confirm Python 3.9+ and `scripts/codex_thread_usage.py` are available.

### Step 1: Restate the requested metric

Distinguish these values before reporting:

- `historical.total_tokens`: processed input plus output across all detected
  monotonic counter segments in the rollout.
- `state_snapshot.tokens_used`: the most recent SQLite cumulative snapshot;
  it can reset after resume or a new Codex process.
- `cached_input_tokens`: a subset of input, not an additional quantity.
- `reasoning_output_tokens`: a subset of output, not an additional quantity.
- `tui_style_total_tokens`: non-cached input plus output; useful for parity with
  the Codex TUI display, but not a billing estimate.

### Step 2: Run the deterministic inspector

Text report:

```bash
python3 "$SKILL_DIR/scripts/codex_thread_usage.py" \
  'codex://threads/<uuid>' --details
```

Machine-readable report:

```bash
python3 "$SKILL_DIR/scripts/codex_thread_usage.py" \
  '<thread-uuid>' --json
```

Use `--codex-home <directory>` only when the user explicitly supplies a
non-default Codex data directory. The script reads message envelopes and token
fields but never emits message bodies.

### Step 3: Evaluate evidence and boundaries

1. Verify the rollout `session_meta.payload.id` matches the deeplink UUID.
2. Compare `state_snapshot.tokens_used` with the last segment total.
3. If there is more than one segment, explain that the SQLite value is only the
   latest counter, while the historical value sums segment terminals.
4. If `estimated_segments` is nonzero, label the total as accumulated or
   estimated rather than exact billing usage.
5. If `raw_response_completed.events` is nonzero, report it separately; it is
   exact per event but may be incomplete for older or provider-specific runs.

### Step 4: Answer concisely

Lead with historical processed tokens, then show input, cached input, output,
reasoning output, the latest SQLite snapshot, segment/reset count, and quality.
Never add cached or reasoning subsets to `total_tokens`. Do not infer money or
subscription quota from these fields.

## Validation

```bash
PYTHONDONTWRITEBYTECODE=1 python3 "$SKILL_DIR/scripts/test_codex_thread_usage.py"
python3 "$SKILL_DIR/scripts/validate_skill.py" "$SKILL_DIR"
```

The documented activation phrase must route here; “查看 Codex 账户剩余额度”
must remain outside this Skill.

## Dependencies

- Python 3.9+ standard library only.
- Read access to the local Codex data directory.
- No credentials, network access, `jq`, or SQLite CLI required at runtime.
