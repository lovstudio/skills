---
name: lovstudio-bp-polish
category: Business
tagline: "Audit and polish an existing BP without changing the facts."
description: >
  Review and improve an existing BP outline, PPTX, PDF, or rendered slide set across
  investment logic, evidence, copy, charts, and visual quality. Produces a scored
  report, page-level revisions, and targeted regeneration instructions while keeping
  facts separate from assumptions. Trigger on "润色 BP", "审稿商业计划书", "PPT 不专业",
  "逐页检查", "改图表", "BP review", "polish pitch deck", or "audit investor deck".
license: MIT
compatibility: >
  Portable Agent Skills format. Python 3.8+ is required for deterministic outline
  auditing. Visual review requires access to rendered slide images or the ability to
  render PPTX/PDF pages. User-specific paths and brand settings come from flags,
  environment variables, or the shared LovStudio profile.
metadata:
  author: lovstudio
  version: "0.1.0"
  tags: business-plan review polish audit evidence charts visual-quality pitch-deck
---

# BP Polish

Improve an existing BP without silently changing its business facts. This skill can
be used before deck production, after rendering, or in a correction loop.

## Modes

| Mode | Input | Focus |
|---|---|---|
| `content` | Outline / Markdown | Product definition, story, copy, page rhythm |
| `evidence` | Outline + ledger/sources | Claims, metrics, TAM/SAM/SOM, assumptions |
| `visual` | PPTX/PDF/slide images | Hierarchy, charts, layout, branding, QR codes |
| `full` | Any complete BP workspace | All dimensions + correction loop |

Infer the smallest useful mode from the request. Do not require a PDF when the user
only wants the outline reviewed.

## Output Contract

```text
business-plan/
├── reports/bp-review.md
├── outline.md                 # patched only when authorized by the request
├── deck-manifest.md           # updated for visual fixes
└── revised slide/deck assets  # only affected artifacts
```

## Workflow (MANDATORY)

### Step 0: Resolve source and mode

Resolve this `SKILL.md` directory as `SKILL_DIR`. Inspect the supplied source and any
existing BP workspace. Reuse audience, stage, style, and evidence definitions.

If multiple review modes are plausible, prefill from the user's wording. Ask one
compact question only when the choice materially changes the work. “不专业” defaults
to `full`; “文字太技术” defaults to `content`; “图表不好看” defaults to `visual`.

Read `references/review-rubric.md`, `references/charts-and-visuals.md`, and
`references/user-config.md` as relevant.

### Step 1: Run deterministic outline audit

When an outline exists:

```bash
python3 "$SKILL_DIR/scripts/audit_bp.py" \
  --input ./business-plan/outline.md \
  --output ./business-plan/reports/bp-review.md
```

Use `--strict` before final delivery. The script checks structure and evidence
hygiene; it does not replace investor judgment or visual inspection.

### Step 2: Review as four adversaries

1. **Non-technical investor** — can the product be repeated after ten seconds?
2. **Category expert** — which product/competition claims are naive or imprecise?
3. **Skeptical partner** — which core claims lack proof or overstate traction?
4. **Design director** — where does layout reduce trust or distort meaning?

For every issue record slide, severity, why it matters, and exact revision.

### Step 3: Protect facts during polishing

- Never make numbers “look better”.
- Never turn an assumption into a fact.
- Never invent a customer quote or testimonial.
- Never widen TAM without a buyer and price bridge.
- Never change a product boundary solely to improve the story.

If a revision needs new evidence, mark an evidence blocker and return it to
`lovstudio-bp-outline`.

### Step 4: Inspect rendered slides

For visual/full mode, create or inspect a contact sheet and every page at normal
presentation size. Check:

- one conclusion per page;
- body text at least 20 pt;
- optical alignment and whitespace;
- chart axes, units, legends, dates, and sources;
- genuine, legible product screenshots;
- unstretched images and logos;
- no clipped text or broken CJK;
- QR codes decoded from final rendered pages;
- clean cover and one-action final page;
- matching PPTX/PDF page counts and normalized filenames.

### Step 5: Apply targeted fixes

Classify each fix:

- **copy fix** — patch outline and regenerate affected slides;
- **evidence blocker** — update ledger/source before rewriting;
- **visual defect** — change layout/style or regenerate affected slides only.

Do not regenerate the whole deck for a one-page issue. Repeat audit → fix → audit for
at most three cycles.

### Step 6: Deliver the report

Lead with verdict and score, then blockers, page-level findings, evidence gaps,
visual QA, and delivery status. Use `assets/templates/bp-review.md`.

Target: 85+ with no blocker. A high numeric score never overrides fabricated data,
missing financing ask, broken source, unreadable slide, or invalid QR code.
