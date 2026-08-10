# Project and HTML contract

## Contents

1. Project structure
2. `brief.md`
3. `project.json`
4. Brand profile
5. Auditable HTML
6. Readiness signal

## Project structure

```text
<project>/
├── source.md
├── brief.md
├── poster.html
├── project.json
├── poster.png
├── audit.json
└── assets/
```

The `scaffold` command creates the first four entries and the asset directory.
Generated files must use UTF-8.

## `brief.md`

Required headings:

```markdown
# Infographic brief

## Audience and decision
## Governing message
## Supporting claims
## Evidence ledger
## Assumptions and gaps
## Visual job
## Deliberate omissions
```

The brief must also record:

- `Title mode: topic | action`
- the display/action title;
- the tail recommendation for `topic` mode;
- why that recommendation belongs after the visual.

An evidence-ledger item should include:

```markdown
- Claim:
  - Exact source:
  - Location:
  - Type: fact | estimate | assumption | interpretation
  - Unit / period:
  - Caveat:
```

## `project.json`

```json
{
  "schema_version": 3,
  "title": "What this infographic helps the reader decide",
  "title_mode": "topic",
  "recommendation": "Evidence-backed advice shown after the visual",
  "aspect": "16:9",
  "template": "comparison-matrix",
  "evidence_mode": "qualitative",
  "canvas": {"width": 1600, "height": 900},
  "brand_profile": "/resolved/path/brand.json",
  "source": "source.md",
  "brief": "brief.md",
  "poster": "poster.html"
}
```

## Brand profile

```json
{
  "schema_version": 1,
  "name": "Skill Publisher",
  "site": "https://example.com",
  "logo": "/absolute/or/profile-relative/logo.svg",
  "primary": "#1F2937",
  "accent": "#4F46E5",
  "ink": "#111827",
  "muted": "#64748B",
  "paper": "#F7F4EF",
  "font_family": "Inter, PingFang SC, Microsoft YaHei, sans-serif",
  "copyright": "本信息图由 Skill Publisher 的「专业信息图」Skill 生成",
  "output_dir": "$HOME/Documents/professional-infographic"
}
```

Logo paths are resolved relative to the profile file, then embedded into the
scaffolded HTML as a data URL. Generated projects do not depend on the original
logo path.

## Auditable HTML

Keep these selectors and attributes:

- `.poster` — fixed canvas and screenshot target;
- `.poster[data-template][data-mode][data-aspect][data-title-mode]` — semantic
  template, evidence mode, canvas, and title strategy;
- `.poster__title[data-audit="title"]` — subject/purpose in `topic` mode or the
  governing conclusion in `action` mode;
- `[data-region="header"]` — compact title and scope region;
- `[data-region="visual"]` — main visual area;
- `[data-region="recommendation"][data-audit="recommendation"]` — evidence-linked
  tail advice required in `topic` mode and omitted in `action` mode;
- `[data-region="footer"]` — notes and ownership;
- `[data-primary-block]` — each main block;
- `[data-encoding]` — space-separated visual variables such as `position color`;
- `[data-data-point]` — plotted or encoded evidence;
- `[data-annotation]` — explanation attached to a visual mark;
- `[data-source-ref="S1"]` — evidence-ledger linkage;
- `[data-decision]` — the mark, outcome, or tail recommendation that carries the
  decision;
- `[data-audit="label"]` — module labels;
- `[data-audit="description"]` — supporting copy;
- `[data-audit="annotation"]` — direct annotation copy;
- `.source-note[data-audit="source"]` — source and caveats;
- `.brand-lockup img` — embedded brand logo;
- `.generation-note[data-audit="attribution"]` — generation attribution.

Each template adds its own semantic selectors; read
`references/visual-grammar.md`. `audit` checks semantic completeness, evidence
linkage, header/visual area ratios, empty blocks, generic card area, copy
budgets, overflow, contrast, and image integrity. Custom layouts may add
selectors but must not remove the contract.

## Readiness signal

Set:

```html
<script>
  window.__INFOGRAPHIC_READY__ = true;
</script>
```

only after asynchronous charts, fonts, and illustrations have settled.
The renderer waits for this signal. For a fully static poster, set it just
before `</body>`.
