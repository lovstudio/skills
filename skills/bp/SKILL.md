---
name: lovstudio-bp
category: Business
tagline: "A composable BP skill kit: outline, deck, and polish."
description: >
  Orchestrate a complete investor BP workflow or route to one focused module:
  source-backed outline, PPTX/PDF production, or evidence/content/visual polishing.
  Use when the user wants to create a business plan end to end, combine BP stages,
  continue from an existing BP workspace, or is unsure which BP skill to use.
  Trigger on "做 BP", "完整商业计划书", "融资 PPT 全流程", "BP skill kit",
  "business plan workflow", "pitch deck pipeline", or "continue my BP".
license: MIT
compatibility: >
  Portable Agent Skills format. The full kit bundles bp-outline, bp-deck, and
  bp-polish in this repository. Python 3.8+ is required for workspace and audit
  scripts. PPTX/PDF generation requires lovstudio-any2deck. User-specific paths,
  brand files, and output directories come from flags, environment variables, or
  the shared LovStudio profile.
depends_on:
  - lovstudio-bp-outline
  - lovstudio-bp-deck
  - lovstudio-bp-polish
metadata:
  author: lovstudio
  version: "0.2.0"
  tags: skill-kit business-plan pitch-deck fundraising outline slides polish audit
---

# BP Skill Kit

Compose only the stages the user needs. The kit preserves the existing
`$lovstudio-bp` entrypoint while exposing three focused skills that can be used
independently.

## Kit Map

| Skill | Input | Output | Use alone when… |
|---|---|---|---|
| `lovstudio-bp-outline` | Project files, links, metrics, interviews | `brief.md`, `evidence-ledger.md`, `outline.md` | The user needs to clarify the investment story first |
| `lovstudio-bp-deck` | Approved outline + evidence + brand assets | PPTX, PDF, preview, deck manifest | The outline already exists and the user wants slides |
| `lovstudio-bp-polish` | Outline, PPTX/PDF, or rendered slides | Scored report + exact revisions + corrected assets | The user already has a BP and wants it made credible/professional |

Default full pipeline:

```text
project evidence
      ↓
bp-outline ── evidence gate ──→ bp-deck ── visual gate ──→ bp-polish
      │                             │                         │
      └ brief / ledger / outline    └ PPTX / PDF / preview   └ report / fixes
```

## Routing Rules

Select the smallest route that fulfills the request:

| User intent | Route |
|---|---|
| “先写 BP 大纲”“梳理融资叙事” | `bp-outline` |
| “大纲已经有了，做成 PPT”“选择 PPT 风格” | `bp-deck` |
| “这份 BP 不专业”“润色/审稿/改图表/改版式” | `bp-polish` |
| “做一份完整 BP”“从项目材料做到 PPT” | `bp-outline → bp-deck → bp-polish` |
| “重写现有 BP 并重新出图” | `bp-polish → bp-deck → bp-polish` |

Do not run all modules merely because they exist. For example, a user asking for an
outline should not wait for image generation.

For the state machine and handoff semantics, read `references/composition.md`.

## Shared Workspace Contract

All modules read and write the same portable workspace:

```text
business-plan/
├── brief.md
├── evidence-ledger.md
├── outline.md
├── assets/
├── deck-manifest.md
├── reports/bp-review.md
├── project-bp.pptx
├── project-bp.pdf
└── project-bp-preview.png
```

Rules:

- Never recreate a file that already contains accepted user work.
- Preserve evidence IDs across modules.
- `outline.md` is the narrative source of truth.
- `deck-manifest.md` records style, slide count, assets, filenames, and render status.
- `reports/bp-review.md` records findings and fixes; it must not silently rewrite facts.
- A later module may send work back to an earlier module when it finds a blocker.

## Orchestration Workflow (MANDATORY)

### Step 0: Resolve the kit

Resolve this `SKILL.md` directory as `KIT_DIR`. Module entrypoints are:

```text
$KIT_DIR/skills/bp-outline/SKILL.md
$KIT_DIR/skills/bp-deck/SKILL.md
$KIT_DIR/skills/bp-polish/SKILL.md
```

Before executing a selected module, read that module's `SKILL.md` completely and
follow its references. If a standalone installation is being used, resolve its own
directory as `SKILL_DIR`.

### Step 1: Inspect context before asking

Inspect the current project, previous BP workspace, supplied deck, conversation, and
links. Reuse known audience, financing stage, ask, language, brand, and output path.

Ask at most one compact round of questions only when an answer changes the result.
If the user says “不要问”“直接做”“按推荐方案”, use these defaults:

- seed-stage investors who may not understand the technology;
- 12–15 slides / 8–10 minutes;
- same language as the user;
- clean editorial style with one brand color;
- PPTX + PDF + preview + review report.

### Step 2: Run the selected module(s)

For each module:

1. announce the module and why it is needed;
2. read its full `SKILL.md`;
3. pass the existing workspace instead of starting over;
4. verify its output contract;
5. continue to the next module only if requested or implied by the chosen route.

### Step 3: Respect the two useful gates

**Evidence gate — after `bp-outline`:**

- product definition is investor-readable;
- all 12 investor questions are covered;
- core numbers have sources or are labeled assumptions;
- no fabricated traction, market, quote, or revenue.

If the user only asked for an outline, stop here. In an interactive full workflow,
show the concise page map and ask whether to produce PPT. Skip this pause when the
user already requested a complete deck or autonomous execution.

**Visual gate — after `bp-deck`:**

- PPTX/PDF/preview exist and page counts match;
- every page has one conclusion and a legible proof;
- logos, images, sources, and QR codes survive final rendering.

Then use `bp-polish` for the final adversarial review.

### Step 4: Handle loop-backs

`bp-polish` may return one of three verdicts:

- **copy fix** → patch the outline and regenerate only affected slides;
- **evidence blocker** → return to `bp-outline`, update the ledger, then regenerate;
- **visual defect** → return to `bp-deck`, regenerate affected slides, and recheck.

Limit automatic correction to three cycles. If a core source remains unavailable,
leave an explicit gap rather than guessing.

### Step 5: Deliver

Return clickable paths to all artifacts created by the selected route. For a full
pipeline, report:

- outline and evidence ledger;
- editable PPTX and PDF;
- full-deck preview;
- deck manifest;
- final review report;
- at most five unresolved decisions or evidence gaps.

## Composition Examples

```text
$lovstudio-bp-outline 根据当前仓库和用户访谈写融资大纲

$lovstudio-bp-deck ./business-plan/outline.md --style minimal

$lovstudio-bp-polish ./business-plan/project-bp.pdf --full

$lovstudio-bp 从当前项目材料生成完整种子轮 BP，不要问，按推荐方案
```

## Backward Compatibility

The original commands remain available:

```bash
python3 "$KIT_DIR/scripts/init_bp.py" --name "Project" --output ./business-plan
python3 "$KIT_DIR/scripts/audit_bp.py" --input ./business-plan/outline.md
```

They delegate to the same templates and rubric used by the child skills.

## Non-Negotiables

- Do not conflate “write an outline” with “produce a finished deck”.
- Do not choose a visual style before the investment narrative is coherent.
- Do not rewrite facts during visual polishing.
- Do not force a user through all modules when one module solves the request.
- Do not finish a full route without PPTX, PDF, preview, and review report.
