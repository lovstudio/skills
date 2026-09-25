---
name: lov-integrate-agent-uiux
description: >
  把 Agent 对话记录、工具过程、状态、Markdown 与输入区集成进 React Native 或 React 应用；触发语包括“接入 AI 对话 UI”与 "integrate agent chat UI"。
license: MIT
metadata:
  author: contributors
  version: "0.1.1"
  card_standard: lovstudio/skill-card/v1
  tags:
    - agent-ui
    - conversation
    - react-native
    - react
    - integration
  compatibility: "Portable Agent Skills format. Python 3.8+; target apps use React Native/Expo or React with TypeScript."
  dependencies: []
---

# Agent 对话界面 · Agent Chat UI

Integrate a production-shaped Agent conversation surface into an existing app.
The deliverable includes a normalized transcript contract, accessible UI
components, target-stack adapters, and a verification report.

## Triggers

### Activate when

- 用户说“参考这个 AI 聊天记录，帮我接入一套 Agent 对话 UI 组件”。
- 用户说“把工具调用、运行状态、Markdown 和输入框整合进现有 App”。
- The user asks to “integrate agent chat UI” or “build reusable AI conversation components”.

### Do not activate when

- 只生成整套新应用外壳；使用 app generator 能力，并将本 Skill 作为可选下游。
- 只修手机端溢出、安全区或响应式布局；使用 mobile adaptation 能力。
- 只连接模型 API、鉴权或计费且不需要对话显示；使用对应 LLM integration 能力。
- 只做视觉重绘、不需要 Agent 消息语义和状态契约；使用 frontend design 能力。

## User Profile (cross-session)

Read `skill.yaml` on every invocation. Resolve user, brand, workspace, shared
preferences, and `skills.lov-integrate-agent-uiux` records without copying
personal values into this portable source. Persist only direct durable user
statements through `scripts/profile_store.py`, then report the saved Profile path.
See `references/user-profile.md`.

## Skill Group Composition

Read `references/skill-composition.md` before composing adjacent capabilities.
Sibling Skills are optional artifact handoffs and never hidden dependencies.

## Required resources

Resolve `SKILL_DIR` from the active Skill context, then verify:

- `$SKILL_DIR/scripts/agent_uiux.py`
- `$SKILL_DIR/assets/common`
- `$SKILL_DIR/assets/react-native`
- `$SKILL_DIR/assets/react`
- `$SKILL_DIR/references/integration-contract.md`
- `$SKILL_DIR/references/yoda-mobile-patterns.md`
- `$SKILL_DIR/references/acceptance-checklist.md`

## Workflow (MANDATORY)

### Step 0: Read context and protect the target

1. Read repository instructions, current working tree state, package manifest,
   UI conventions, existing chat components, and supported platforms.
2. Read the shared Profile using `scripts/profile_store.py read --skill-id
   lov-integrate-agent-uiux --pretty` when a Profile is configured.
3. Preserve unrelated edits. Do not overwrite an occupied component directory
   unless the user explicitly authorizes replacement and the old files are backed up.
4. Read `references/integration-contract.md` and
   `references/yoda-mobile-patterns.md` before designing the adapter.

### Step 1: Audit the host application

Run the deterministic audit:

```bash
python3 "$SKILL_DIR/scripts/agent_uiux.py" audit <project-path> --format json
```

Confirm the detected stack, source root, package manager, existing design tokens,
message data source, send/retry contract, realtime mechanism, and test commands.
If the stack is not React Native/Expo or React Web, use the neutral contract as
the implementation source and state that the bundled scaffold is unavailable.

### Step 2: Map real data to the normalized contract

Create one adapter from the host's transport/domain objects to `AgentMessage`,
`AgentSessionState`, `AgentAttachment`, and `PendingInteraction`. Keep API calls,
SSE/WebSocket/polling, persistence, and provider-specific fields outside the UI
components. Preserve stable message and tool-call IDs.

Required semantic coverage:

- user, assistant, tool, and status roles;
- commentary versus final assistant phases;
- running, completed, and failed tool states;
- Markdown, plain text, and code;
- pending choice, confirmation, or text interactions;
- session working, waiting, error, completed, and idle states;
- idempotent send/retry identity and preserved composer draft on failure.

### Step 3: Scaffold the target-stack components

Preview first:

```bash
python3 "$SKILL_DIR/scripts/agent_uiux.py" scaffold <project-path> --dry-run
```

Then scaffold into the detected source tree:

```bash
python3 "$SKILL_DIR/scripts/agent_uiux.py" scaffold <project-path>
```

Use `--stack react-native` or `--stack react` only to override a wrong detection.
Use `--component-dir <relative-path>` to follow an established component layout.
The command refuses occupied targets; do not use `--force` without explicit user
authorization. Import files directly from their source modules rather than
adding a re-export barrel when the host forbids re-exports.

### Step 4: Integrate into the real screen

1. Bind normalized messages, session state, pending interaction, draft, and send
   callback to `AgentConversation`.
2. Map host design tokens into `AgentUiTheme`; do not hard-code product branding.
3. Keep the newest content visible only while the user is already near the end;
   expose a jump-to-latest control otherwise.
4. Group adjacent tool events and keep tool details collapsed by default.
5. Keep input editable and preserved across recoverable send failures. Surface a
   copyable request/context ID in diagnostics without exposing secrets.
6. Add loading, empty, offline, waiting, error, disabled, and long-content states.
7. Preserve keyboard, safe-area, screen-reader, reduced-motion, localization, and
   minimum touch-target behavior of the host platform.

### Step 5: Verify the integrated result

Run the structural verifier:

```bash
python3 "$SKILL_DIR/scripts/agent_uiux.py" verify <project-path>
```

Then run the host's format, lint, typecheck, tests, and build commands. Exercise
the smallest real end-to-end conversation covering user text, assistant Markdown,
a running then completed tool group, a pending interaction, send failure/retry,
and a final response. For native mobile changes, follow the host repository's
real-device requirement; a static build is not device verification.

Apply every item in `references/acceptance-checklist.md`. Record the real input,
minimum prompt, output paths, commands, and observed evidence in the task result.
Do not invent screenshots, scores, latency wins, or device proof.

## Output contract

Return:

- the detected stack and normalized data mapping;
- created or changed component and adapter paths;
- supported conversation states and any consciously deferred state;
- structural verification plus host test/build/runtime evidence;
- remaining gaps, especially realtime, device, accessibility, or provider limits.

## Dependencies

- Skill runtime: Python 3.8+; PyYAML only for validating the Skill itself.
- React Native scaffold: `react`, `react-native`; Expo is supported but optional.
- React Web scaffold: `react`, `react-dom`; no UI or Markdown package is required.
- Host-specific icons, animation, Markdown, transport, and state libraries remain optional.
