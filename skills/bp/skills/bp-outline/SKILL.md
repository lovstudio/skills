---
name: lovstudio-bp-outline
category: Business
tagline: "Project evidence → investor narrative and 12–15 slide BP outline."
description: >
  Turn existing project materials into a source-backed investor BP brief, evidence
  ledger, and 12–15 slide outline. Use before making slides, when the product
  positioning is unclear, or when an existing outline is too technical, generic,
  or unsupported. Trigger on "写 BP 大纲", "融资叙事", "梳理商业计划书",
  "先不要做 PPT", "BP outline", "investor narrative", or "pitch deck outline".
license: MIT
compatibility: >
  Portable Agent Skills format. Python 3.8+ is required only for workspace
  initialization. Current market, competitor, and policy claims require access to
  authoritative sources. Workspace and brand paths come from flags, environment
  variables, or the shared LovStudio profile.
metadata:
  author: lovstudio
  version: "0.1.0"
  tags: business-plan outline investor narrative evidence market positioning
---

# BP Outline

Build the investment story before choosing a visual style. This skill stops at an
approved, source-backed outline and does not generate PPTX/PDF.

## Input

Any combination of:

- repository, product docs, PRD, website, prior applications, or existing BP;
- analytics exports, payment/usage data, GitHub evidence, and customer notes;
- product screenshots, founder profile, team history, brand assets;
- financing stage, amount, equity/instrument, and milestones.

## Output Contract

```text
business-plan/
├── brief.md
├── evidence-ledger.md
├── outline.md
└── assets/
```

The output is ready for `lovstudio-bp-deck` only when the evidence gate passes.

## Workflow (MANDATORY)

### Step 0: Resolve the skill and workspace

Resolve this `SKILL.md` directory as `SKILL_DIR`. If the user already has a
`business-plan/` workspace, continue in it. Otherwise initialize one:

```bash
python3 "$SKILL_DIR/scripts/init_bp.py" \
  --name "Project Name" \
  --stage seed \
  --output ./business-plan
```

Read `references/user-config.md` for portable path and brand resolution.

### Step 1: Inspect before asking

Search the user's supplied scope first. Prefer exact repo/files/URLs over broad
discovery. Extract known audience, financing stage, ask, product, buyer, traction,
business model, market, competition, growth, and team evidence.

Ask at most one compact round of questions for missing decisions that materially
change the outline. If the user says “不要问”“按推荐方案”, assume seed investors,
12–15 slides, 8–10 minutes, and mark the financing ask as a visible gap if unknown.

### Step 2: Build the evidence ledger

Record every material claim as:

- fact;
- inference;
- assumption;
- missing.

Include source, as-of date, slide destination, and next action. For changing claims,
verify current authoritative sources. Never substitute a broad AI forecast for a
buyer-linked market calculation. Read `references/evidence-and-market.md`.

### Step 3: Define the investor-readable product

Before the vision, draft three one-line definitions:

1. literal category;
2. accurate comparator (“X for Y”);
3. category-creation language with a plain-language explanation.

Choose the line a non-technical investor can repeat after ten seconds. Separate:

```text
early wedge → adjacent users → long-term market
```

Treat technical modes as implementation unless the buyer actually pays for the
mechanism. Read `references/investor-story.md`.

### Step 4: Write the 12–15 page argument

Use this 12-page base:

1. one sentence: who you are;
2. concrete user problem;
3. how the product solves it;
4. product demo or core experience;
5. why now;
6. real validation;
7. business model;
8. market size and wedge;
9. competition and differentiation;
10. growth plan;
11. why this team;
12. financing ask, use, and next proof.

Expand only when a product demo, moat, B2B deployment model, or financial model
needs a dedicated page. Read `references/deck-architecture.md`.

Each slide entry must contain:

- conclusion headline;
- investor takeaway;
- evidence IDs and sources;
- exact visual/chart proof;
- speaker purpose;
- unresolved gap or “none”.

### Step 5: Run the evidence gate

The outline is ready only when:

- all 12 investor questions are covered;
- the product definition is investor-readable;
- every core number traces to evidence or a labeled assumption;
- traction stages and denominators are not mixed;
- TAM/SAM/SOM has a buyer-price-reachability bridge;
- the financing ask connects to 18–24 month validation milestones;
- no placeholder is hidden as final copy.

Report the page map and at most five evidence gaps. Do not start slide generation
unless the user asked for a complete BP or explicitly continues with `bp-deck`.

## Recommended Next Step

```text
$lovstudio-bp-deck ./business-plan/outline.md
```
