---
name: lov-yoda-automation
description: >
  在 Yoda 中创建、修复、核验和停用一次性或周期自动化；适用于“设置 Yoda 提醒”“每个工作日巡检”“修复 cron”“automation schedule”等请求，输出可核验的计划、下次运行和运行记录。
license: MIT
allowed-tools:
  - computer-use
  - shell
metadata:
  author: LovStudio
  version: "0.2.0"
  card_standard: lovstudio/skill-card/v1
  tags:
    - yoda
    - automation
    - scheduler
    - cron
    - notification
  compatibility: "Yoda with native Automations, plus Python 3.8+ for read-only verification."
  dependencies: []
---

# lov-yoda-automation

将自然语言的提醒、巡检或定期跟进需求收敛为一条可回读的 Yoda 原生自动化；交付明确的时区、cron、下次运行、通知内容、完成门和运行证据。

## Triggers

### Activate when

- 用户说“在 Yoda 里每个工作日 10 点提醒我”“设置周期自动化”“修复 Yoda cron”。
- 用户说“这个自动化没有下次执行”“不要重复通知”“完成后停用提醒”。
- User asks to “create a Yoda automation”, “schedule a recurring Yoda reminder”, or “verify an automation run”.

### Do not activate when

- 只需要一次性聊天提醒且不需要持久化计划；直接在当前对话中回应。
- 目标是飞书消息投递；交给 `feishu-cron-reminder`。
- 目标是通用 Zapier、Make 或 n8n 流程设计；交给 `automation-workflows`。

## User Profile (cross-session)

Read the shared `user-profile/v1` contract declared by `skill.yaml` on every run. Resolve timezone and notification preferences from the current request first, then Skill records and shared profile values. Persist only direct, durable user statements through `scripts/profile_store.py`; keep credentials, private paths and task-specific financial details out of the Skill source.

## Skill Group Composition

Read `references/skill-composition.md` before selecting an adjacent capability. This is a standalone Skill: external Skills are optional handoffs, never hidden runtime dependencies.

## Workflow

### Step 0: Resolve runtime and inspect the existing automation

1. Reuse the current Yoda instance and inspect the Automations page or the host's native automation API.
2. Search by the user-visible purpose and stable task identifier. Read title, status, trigger kind, cron, timezone, next run, latest run and its error.
3. If a matching automation exists, edit that record. Do not create a second active reminder for the same purpose.
4. Read `references/schedule-contract.md` and `references/run-evidence.md` before changing a schedule.

### Step 1: Translate the request into a schedule contract

1. State the recipient, action, frequency, timezone, notification text, completion gate and stop action.
2. Convert recurring schedules to a valid five-field cron expression. For every weekday at 10:00 in Beijing, use `0 10 * * 1-5` with `Asia/Shanghai`.
3. A one-off timestamp is not a cron expression. Store it as the host's one-time trigger or convert the request to an explicit recurring cron only when the user asked for recurrence.
4. Set a future `next_run_at` and show it in both local time and ISO-8601 UTC. On Sunday, August 16, 2026, the next Beijing weekday 10:00 occurrence is Monday, August 17, 2026, 10:00 (`2026-08-17T02:00:00.000Z`).

### Step 2: Configure Yoda native automation

1. Keep `trigger_kind`, `cron_expr`, `timezone`, `schedule_label`, `status`, and `next_run_at` internally consistent.
2. Write a focused prompt that matches the requested outcome. A reminder automation should notify the user; it must not silently turn into an outbound call, payment, upload, or new task.
3. Include the concrete information the user needs at trigger time, then put long context in collapsible details or the automation body rather than the title.
4. Use Yoda native automation first. Introduce an external scheduler only when Yoda cannot meet the requirement or the user explicitly selects another platform; disable the replacement to prevent duplicate notifications.

### Step 3: Verify before declaring completion

1. Re-read the saved record after the write. Verify active status, cron syntax, timezone, a future next run, and exact notification intent.
2. For a SQLite-backed host, run:

```bash
python3 "$SKILL_DIR/scripts/verify_automation.py" \
  --db DATABASE_PATH --id AUTOMATION_ID \
  --expect-cron '0 10 * * 1-5' \
  --expect-timezone Asia/Shanghai
```

3. Read the most recent run. A prior failure such as an app exit is historical evidence, not proof that the repaired future schedule will run.
4. Report the automation title, schedule, timezone, next execution, status, latest-run state and completion/stop rule. Include the script's copyable `context_id` if validation fails.

### Step 4: Handle completion and failures

1. Pause the exact automation after the user confirms the completion gate, then read the record back as paused.
2. If the run fails, preserve the current task and record the failure message, then repair the schedule or runtime dependency behind it.
3. Do not report a recurring reminder as active until a native record with a future `next_run_at` has been read back.

## Dependencies

- Yoda native Automations UI or host API.
- Python 3.8+ for the optional read-only SQLite verification CLI.
- No credentials are stored by this Skill.

## 通用反馈闭环

用户在 Skill 驱动任务中提出修改意见时，继续当前产物前必须执行：

1. 先判断意见是 `task-specific`（仅本次）还是 `reusable`（可跨任务复用）。
2. `task-specific` 只修改当前任务，不改 Skill。
3. `reusable` 先确定作用域：领域规则先更新对应 canonical Skill；适用于所有 Skill 的规则先更新共享规范。
4. 完成规则更新、版本、lint 与分发核验后，再把修改应用到当前任务。
5. `reusable` 修改会使此前的“确认”“继续”“发吧”失效；完成当前产物修改和回读后必须停下，等待用户下一步指示，不自动进入发布、提交或其他外部写入。
