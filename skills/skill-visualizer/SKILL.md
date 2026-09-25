---
name: lov-skill-visualizer
description: >
  把本地 Agent Skill 目录或 SKILL.md 解析成场景先行的一页式信任审阅、内部
  运行图和 JSON 模型；先说明什么时候非它不可，再连续展示输入、内部转化、
  交付结果、源码依据与未证明缺口。当用户要理解、审阅或信任一个 Skill 时使用。
license: MIT
depends_on:
  - lov-branding-consistency
metadata:
  author: contributors
  version: "0.6.1"
  card_standard: lovstudio/skill-card/v1
  tags:
    - skill-visualization
    - mermaid
    - workflow
    - static-analysis
  compatibility: "Python 3.8+ and PyYAML; generated HTML embeds Mermaid 11.12.2 and works offline in a modern browser."
  dependencies:
    - python3
    - PyYAML
---

# Skill 透视镜 · Skill Lens

Turn one local Skill into a scenario-first trust brief rather than an evidence
explorer. The standalone HTML answers when the Skill is the right choice, shows
its input-to-outcome transformation as one uninterrupted reading path, and then
separates source declarations, supporting capability, checks, and unproven
effect. Mermaid remains editable secondary evidence, not the primary interface
and not proof that the target Skill works.

## Triggers

### Activate when

- 用户提供本地 Skill 目录或 `SKILL.md`，说“画出这个 Skill 的运行逻辑”。
- 用户说“把 Skill 的触发、步骤、分支和依赖生成 Mermaid 流程图”。
- The user says “visualize this skill workflow” or “generate a Mermaid diagram for this Skill”.

### Do not activate when

- 用户只要把已经整理好的流程美化成通用 SVG；交给通用 diagram renderer。
- 用户要审计并修改 Skill 质量、版本或分发同步；交给 `lov-skill-optimizer`。
- 用户要展示多个 Skill 之间的目录依赖，而非单个 Skill 的运行契约；使用目录依赖可视化能力。

## User Profile (cross-session)

Every generated Skill is connected to the shared `user-profile/v1` contract in
`skill.yaml`. Read the shared user, brand, workspace, preferences, and this
Skill's `skills.<skill_id>` namespace at the start of every run. Keep the source
portable: resolved personal values belong in the shared profile, never here.

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
export SKILL_DIR="/path/to/lov-skill-visualizer"
```

Resolve `context.profile` on every invocation. The precedence is current request,
project context, Skill-specific profile records, shared preferences, shared
brand/user profile, then safe defaults. A direct user statement about a durable
preference or brand fact should be saved with `scripts/profile_store.py record`
using `--confirm`, followed by a concise saved-path report.

### Step 1: Understand the requested outcome

- Resolve the explicit Skill directory or `SKILL.md` path. Resolve symlinks, but
  show only Skill-relative paths in the report.
- Default to a Markdown report with Mermaid, a sibling standalone HTML review,
  and a JSON model. Respect explicit output paths, diagram direction, language,
  or reference depth.
- If the user supplied a valid target, do not ask them to choose parser or
  renderer machinery. Mermaid is the default because it remains editable.

### Step 1.5: Analyze nearby Skills before implementation

- Inspect related local and installed Skills by routing contract and concrete
  input/output, not by filename alone.
- Record upstream, core, downstream, overlap, and not-composed decisions in
  `references/skill-composition.md`.
- Keep sibling Skills optional and artifact-based. When stages require hard
  coupling for one outcome, create a self-contained Kit instead.

### Step 2: Extract the declared runtime contract

Run the standalone extractor:

```bash
python3 "$SKILL_DIR/scripts/visualize_skill.py" "$TARGET_SKILL" \
  --output "$OUTPUT_MARKDOWN" \
  --json "$OUTPUT_JSON" \
  --language auto \
  --direction TB \
  --max-depth 2
```

`--output path/report.md` also writes `path/report.html` by default. Use
`--html path/custom.html` to choose another location or `--no-html` when the
standalone review is intentionally not required.

- Accept either a Skill directory or its `SKILL.md`.
- Extract routing examples, workflow steps, explicit conditional rules,
  frontmatter dependencies, Profile runtime context, Skill Kit pipelines, and
  local resources reachable from the controller.
- Preserve each step's authored actions, criteria, decisions, guardrails,
  commands, and verification instructions as line-bound detail items.
- Parse embedded Kit module workflows and quality gates, then associate a
  controller step only when the module or pipeline is explicitly named.
- Build a trust model that separates traceable declarations, supporting
  modules/resources, deterministic implementation, declared checks, observed
  artifacts, and unproven runtime effect.
- Follow linked local Markdown references up to `--max-depth`. Inventory
  packaged scripts, references, assets, and modules even when they are not
  linked, so dead or implicit resources remain visible.
- Treat only declared text as fact. Do not invent a branch, dependency, or
  success state to make the diagram look complete.

Read `references/logic-model.md` for the JSON fields, extraction rules, Mermaid
structure, and known static-analysis limits.

### Step 3: Review diagnostics and evidence

- Every extracted trigger, step, and condition keeps a relative file and line
  span. Use those spans to resolve ambiguity in the source instead of guessing.
- `error` diagnostics mean the report is structurally incomplete, such as a
  missing workflow or referenced file. `warning` and `info` preserve useful
  gaps without blocking an exploratory report.
- Use `--strict` when the report is part of a quality gate. Exit code `3` means
  extraction completed but at least one error diagnostic remains; exit code
  `2` means the target or runtime could not be processed.
- Open the standalone HTML in a browser for review. The first screen must answer
  what concrete situation justifies this Skill and what cross-step problem it
  solves. Do not begin with coverage metrics, an abstract feature list, or a
  graph the reviewer must explore.
- The primary runtime graph starts at internal execution. Activation and
  non-trigger examples belong to an explicitly external, collapsed host-routing
  section and must never appear as a yes/no branch in the internal graph.
- Turn the selected workflow or Kit pipeline into one fixed, fully visible
  narrative: starting state, internal transformations, resulting state, why the
  Skill is a better fit than narrower tools, and the explicit non-use boundary.
- Do not require node clicking, dragging, zooming, tab switching, or an evidence
  inspector to understand the primary logic. The reviewer must be able to read
  the complete path by scrolling once.
- Keep rendered Mermaid views for internal runtime, resources, and optional Kit
  pipelines inside one secondary technical-evidence disclosure. Nodes are not
  navigation controls. Raw Mermaid, routing, resources, diagnostics, and JSON
  remain available for verification after the conclusion.
- Resolve `records.html_review_presentation` from the shared Profile. Default to
  a restrained, purpose-first layout. When the resolved language is Chinese,
  localize interface and display labels wherever semantics can be preserved;
  keep filenames, paths, Skill IDs, commands, source code, and Mermaid syntax in
  their original form.
- Resolve `records.review_narrative` as the presentation contract. Prefer a
  scenario-first single page, read-only linear logic, and collapsed technical
  evidence. Do not turn evidence coverage into a generic card wall.
- The HTML embeds all CSS, JavaScript, Mermaid 11.12.2, Mermaid source, and JSON,
  so it requires no network or hosted renderer. Use optional downstream
  renderers only for alternate presentation formats.

### Step 4: Validate the deliverable

- Confirm the requested Markdown, HTML, and JSON output files exist and are
  UTF-8 readable.
- Check that the Markdown contains Mermaid `flowchart` blocks and that the JSON
  declares `lovstudio/skill-logic/v1`.
- Check that the HTML contains the embedded `logic-model`, has no external
  scripts or stylesheets, and remains usable at desktop and mobile widths.
- Confirm technical evidence is closed by default, Chinese display labels are
  present for a Chinese report, and the extracted JSON model remains unchanged.
- Assert that the primary page contains no node selector, zoom control, diagram
  tabs, or button-driven evidence workspace.
- Use a real browser to require every declared Mermaid host to contain an SVG
  after rendering, external routing to remain absent from the runtime graph,
  the linear stages to fit the desktop layout, and the page itself to avoid
  horizontal overflow at mobile width.
- Report extracted step, condition, linked-resource, and missing-resource
  counts. Preserve diagnostics in the handoff; a generated file is not proof of
  full coverage.
- For source validation, run `python3 scripts/validate_skill.py .`; for focused
  parser tests, run `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests`.

## Dependencies

- Python 3.8 or newer.
- PyYAML for frontmatter and manifest parsing.
- Vendored Mermaid 11.12.2 browser runtime under `assets/vendor/`.
- No Mermaid CLI, network access, or sibling Skill is required to generate or
  review the outputs. A modern browser renders the embedded runtime.
