---
name: lov-align-wechat-uiux
description: >
  系统诊断并修复产品与微信官方在消息、会话、联系人、朋友圈及交互上的语义和 UIUX 偏差；适用于“对齐微信官方”“这条微信消息显示不对”、"fix WeChat UI parity" 或 "audit WeChat behavior"。
license: MIT
depends_on:
  - lov-branding-consistency
metadata:
  author: contributors
  version: "0.2.1"
  tags:
    - wechat
    - ui-parity
    - message-semantics
    - product-quality
  compatibility: "Portable Agent Skills format. Requires repository inspection tools; optional image inspection, web research, and app runtime validation."
  dependencies: []
---

# 微信体验校准 · WeChat Experience Alignment

Repair WeChat-facing product behavior from the data contract outward. A mismatch
is rarely only CSS: it may expose incorrect message classification, identity
resolution, state modeling, interaction semantics, or missing regression proof.

## Triggers

### Activate when

- 用户说“这个 UIUX 和微信官方不一致”“对齐微信官方”“这条微信消息显示不对”。
- 用户提供微信截图、XML、数据库记录或消息类型，要求还原微信中的真实表现。
- 用户要求系统检查聊天、会话列表、联系人、朋友圈、媒体或系统提示的微信一致性。
- The user asks to fix WeChat UI parity, reproduce official WeChat behavior, or audit a WeChat-compatible experience.

### Do not activate when

- 用户只要求建立连接、解密数据库或恢复附件，尚未涉及产品语义和界面表现。
- 用户只要求制作营销页面、品牌视觉或与微信产品体验无关的通用前端组件。
- 用户明确只要只读代码审查且不以微信官方体验为基准；使用普通代码审查能力。

## Core contract

- **Evidence before imitation.** Treat screenshots, raw records, runtime state,
  official documentation, and version/platform context as separate evidence.
- **Storage type is not product meaning.** Database type, nested app type, subtype,
  XML fields, sender identity, and presentation type must be modeled explicitly.
- **Fix the earliest broken layer.** A renderer workaround is incomplete when the
  parser, canonical model, shared presentation, export, search, or diagnostics
  still disagree.
- **Official grammar before decorative similarity.** Match hierarchy, control
  meaning, density, alignment, state, timing, copy, and interaction before pixels.
- **One semantic source.** Chat view, search, copy, export, notifications, and
  analysis should consume the same normalized presentation contract.
- **Proof follows the user path.** Compilation and HTTP success are supporting
  checks; the requested message or interaction must be observed in the real
  surface whenever the runtime is available.

## Skill Kit Modules

Load every selected module completely before acting:

- `$SKILL_DIR/skills/wechat-evidence/SKILL.md` — establish official, product, raw-data, code, and runtime evidence.
- `$SKILL_DIR/skills/wechat-semantics/SKILL.md` — define the canonical WeChat meaning and find the earliest broken layer.
- `$SKILL_DIR/skills/wechat-ui-parity/SKILL.md` — implement official interaction grammar using the product's existing design system.
- `$SKILL_DIR/skills/wechat-parity-validation/SKILL.md` — validate parser, presentation, visual, runtime, and downstream parity.

`kit.yaml` is the module and pipeline manifest. Read
`$KIT_DIR/references/parity-model.md`,
`$KIT_DIR/references/wechat-surface-grammar.md`, and
`$KIT_DIR/references/acceptance.md` when running the full fix or audit pipeline.

## Workflow (MANDATORY)

### Step 0: Resolve the actual target

1. Read project instructions and inspect the current git/worktree state.
2. Start from the exact screenshot, raw record, URL, message identity, component,
   or error supplied by the user.
3. Identify product surface, WeChat platform/version, repository package, current
   runtime, and whether the request authorizes implementation or only audit.
4. Preserve unrelated changes. Confirm the real worktree or process before
   claiming runtime behavior.

If the user asks “为什么不一致” without excluding edits, diagnose and repair.
Use the `audit` pipeline only when the user explicitly requests read-only output.

### Step 1: Select a pipeline

| Situation | Pipeline |
|---|---|
| A concrete mismatch should be fixed | `fix-parity` |
| A product area should be audited systematically | `audit-parity` |
| Raw data is being classified incorrectly | `model-semantics` |
| An existing fix needs acceptance | `verify-parity` |

For `fix-parity`, run in order:

1. `wechat-evidence`
2. `wechat-semantics`
3. `wechat-ui-parity`
4. `wechat-parity-validation`

Do not skip semantics because the screenshot looks simple.

### Step 2: Build a parity case

Create an internal case using `references/acceptance.md`. Capture:

- stable case ID and surface;
- official/reference evidence and platform/version;
- current product evidence;
- raw data or event shape, including direct and nested types;
- canonical semantic type, participants, content source, state, and identity;
- expected layout, copy, controls, states, interactions, and forbidden artifacts;
- affected consumers such as chat, search, export, copy, analysis, and diagnostics;
- planned parser, component, visual, runtime, and regression checks.

When a reusable JSON artifact helps, start from
`$KIT_DIR/assets/parity-case.example.json` and validate it with:

```bash
python3 "$KIT_DIR/scripts/validate_parity_case.py" CASE.json
```

The JSON is an internal engineering contract, not product-facing copy.

### Step 3: Establish the evidence hierarchy

Run `wechat-evidence` and classify each input:

1. observed official behavior on the matching platform/version;
2. official protocol or product documentation;
3. exact raw record and decoded structure;
4. observed current product behavior;
5. repository implementation and tests;
6. inference, labeled internally.

A single screenshot proves appearance in one state. It does not alone prove
storage meaning, hover behavior, accessibility, export behavior, or all versions.
If official behavior is time-sensitive or unclear, verify it with current primary
evidence. Avoid broad web research when the supplied fixture and local code are
already sufficient.

### Step 4: Model the canonical meaning

Run `wechat-semantics` before editing UI:

1. Parse XML/JSON/database structures by hierarchy, not first-match regex.
2. Separate transport/storage types from canonical product types.
3. Resolve sender, target, conversation, direction, content source, subtype,
   actionability, and time behavior.
4. Preserve raw content and stable source identity for debugging and exact locate.
5. Define one presentation payload consumed by every downstream surface.
6. Locate the earliest layer where observed data diverges from the contract.

Classify the root cause as one or more of:

- acquisition or decoding;
- identity or direction;
- structural parsing;
- canonical type or state;
- presentation contract;
- component selection;
- visual grammar;
- interaction/accessibility;
- downstream consumer drift;
- verification gap.

### Step 5: Implement from model to pixels

Run `wechat-ui-parity` in this order:

1. Add or update a realistic raw fixture.
2. Fix decoding, identity, parsing, and canonicalization as needed.
3. Extend the shared presentation payload.
4. Route to the correct existing component family.
5. Adjust layout, type, color, spacing, assets, and motion last.
6. Update search, copy, export, context menu, notifications, and analysis when
   they consume the same semantic object.

Reuse adjacent primitives and tokens. A system event is content, not a fake
message bubble; status is not a button; secondary actions belong in a compact
menu when they would crowd the primary path. Inputs must preserve IME composition.
Error UI must offer copyable user-facing detail and useful diagnostic context.

### Step 6: Validate the complete path

Run `wechat-parity-validation` and verify proportionally to risk:

- fixture and parser assertions;
- canonical presentation and downstream consumer assertions;
- component semantics, accessibility name, keyboard, IME, and control states;
- narrow and wide layout, long text, missing assets, dark/light themes if present;
- current official reference comparison;
- real runtime path with the exact record or closest deterministic fixture;
- package tests, typecheck, lint, build, and diff hygiene;
- integrated branch or `main` after merge when project rules require it.

If the runtime is unavailable, report that specific evidence gap while still
completing deterministic verification. Never label a case `verified` from CSS or
build output alone.

### Step 7: Report the outcome

Lead with what now matches the official behavior. Include:

- root cause and earliest broken layer;
- canonical semantic contract established;
- user-visible UI and interaction changes;
- downstream consumers updated;
- tests and observed runtime evidence;
- remaining platform/version or device gaps;
- exact files, commits, and merge state when code changed.

Keep internal reverse-engineering notes and raw identifiers out of user-visible
product copy. Preserve them only in diagnostics, fixtures, and engineering output.

## Dependencies

No fixed frontend framework. Use the target repository's package manager, design
system, test stack, and runtime. The optional parity-case validator uses Python
3.8+ standard library only; Skill source validation additionally uses PyYAML.

## Runtime context (shared)

运行前读取本 Skill 包的 `skill.yaml`，由宿主提供 `skill-runtime/v1` 上下文。字段解析顺序为：当前请求、项目上下文、个人 Preferences、品牌 Profile、通用默认值。

- 只使用 Manifest 声明的字段；Profile 保存公开品牌事实，Preferences 保存个人工作偏好。
- `required: true` 字段缺失时，按 Manifest 的问题配置向用户提出一个聚焦问题；用户明确同意后再保存回答。
- 报错提供可复制的 `context_id`、字段路径与来源，诊断内容避开秘密、完整私人路径和原始配置。
