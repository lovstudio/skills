---
name: lov-wechat-parity-validation
description: >
  验证微信体验修复是否同时覆盖解析、共享表现、视觉交互、下游消费者与真实运行时；适用于“验收微信对齐”“还有没有漏改”、"review the parity fix" 或 validate WeChat behavior。
license: MIT
metadata:
  author: contributors
  version: "0.1.1"
  tags:
    - wechat
    - validation
    - regression
    - visual-qa
  compatibility: "Portable Agent Skills format with target project test, build, and optional runtime tools."
  dependencies: []
---

# 微信对齐验收 · WeChat Parity Review

Prove that the semantic object, every important consumer, and the observed user
path agree with the intended WeChat behavior.

## Triggers

### Activate when

- 用户说“验收微信对齐”“还有没有漏改”“确认这个修复真的生效”。
- 已有 parity 修复或案例契约，需要做解析、UI、下游和运行时回归。
- The user asks to review the parity fix, validate WeChat behavior, or find missing regressions.

### Do not activate when

- 用户尚未提供目标行为、官方参考或可推导的体验契约。
- 用户只要求通用性能测试、安全审计或发布，不涉及微信一致性。

## Workflow (MANDATORY)

### Step 1: Validate the case contract

Confirm that official evidence, product observation, raw structure, canonical
meaning, UX expectations, forbidden artifacts, affected consumers, and planned
checks are present. If a JSON case exists, run the bundled validator.

### Step 2: Validate data and semantics

- Positive raw fixture maps to the intended canonical type and payload.
- Nearest negative fixture does not match.
- Direct and nested types retain hierarchy.
- Sender, target, direction, stable source identity, and raw diagnostics survive.
- Unknown or future variants fail legibly rather than leaking raw structures.

### Step 3: Validate downstream consistency

Check chat view, search result, copy text, export, notifications, archives,
analysis, and diagnostics according to actual product scope. Every consumer should
use the shared presentation or document an intentional difference.

### Step 4: Validate interaction and visuals

- Correct component family, layout ownership, grouping, avatar, bubble, metadata;
- typography, wrapping, emoji/media behavior, spacing, color, and theme;
- keyboard, focus, accessible names, context menu, copy, selection, links, IME;
- normal, hover, pressed, loading, disabled, error, missing, and long-content states;
- narrowest supported width and regular desktop width.

Compare against the matching official platform/version, not a mixed reference.

### Step 5: Validate the real path

Prefer the exact database record or deterministic fixture inside the actual app.
Confirm the running worktree/process before inspection. A build, toast, or test
pass does not replace observing the requested state.

If device or app state blocks runtime observation, record only that evidence gap;
keep deterministic results separate and do not label the case fully verified.

### Step 6: Run engineering gates

Run the repository-native focused tests, full relevant tests, typecheck, lint,
build, diff checks, and integration checks. Re-run after merge when `main` is the
required completion state.

### Step 7: Issue the verdict

Use one status:

- `verified` — semantics, consumers, UI, and requested runtime path observed;
- `implemented` — code and deterministic gates pass, runtime evidence remains;
- `modeled` — evidence and canonical contract exist, implementation pending;
- `observed` — discrepancy is evidenced but root cause is open.

Report exact proof and gaps. Never upgrade status because a lower layer passed.

## Dependencies

None beyond the target project's own quality gates and optional runtime inspection.

## Runtime context (shared)

运行前读取本 Skill 包的 `skill.yaml`，由宿主提供 `skill-runtime/v1` 上下文。字段解析顺序为：当前请求、项目上下文、个人 Preferences、品牌 Profile、通用默认值。

- 只使用 Manifest 声明的字段；Profile 保存公开品牌事实，Preferences 保存个人工作偏好。
- `required: true` 字段缺失时，按 Manifest 的问题配置向用户提出一个聚焦问题；用户明确同意后再保存回答。
- 报错提供可复制的 `context_id`、字段路径与来源，诊断内容避开秘密、完整私人路径和原始配置。
