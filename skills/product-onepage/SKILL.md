---
name: lov-product-onepage
description: Turn a product brief, current conversation, URL, repository, Markdown, screenshots, or research into a brand-led OnePage promotional poster with truthful conversion copy, real product proof, editable HTML/SVG, and high-resolution PNG. Use when the user asks for a product launch poster, 产品宣发海报, 产品介绍长图, 应用发布图, 一页产品故事, launch one-pager, product marketing one-page, social campaign poster, or a static poster distilled from a Landing Page.
depends_on:
  - lov-branding-consistency
---

# 产品一页纸 · Product OnePage

Build one public product story on one fixed canvas. Combine brand positioning,
conversion narrative, evidence discipline, product staging, and code-rendered
typography. Do not turn a Landing Page into a screenshot or an infographic into
a card wall.

```text
source truth
→ public/private ledger
→ Brand Spine + one public thesis
→ headline spine + conversion
→ layout × art direction
→ real product stage + supporting visual
→ editable HTML/SVG master
→ render + machine gate
→ full-size and thumbnail review
→ independently recomposed derivatives
```

Default to a `4:5` master at 1080 × 1350. Recompose `9:16`, `1:1`, `16:9`, and
`A4` derivatives; never crop or uniformly shrink the master.

## Required outcome

Deliver:

- one recognizable product thesis, not a feature inventory;
- clear category, audience relevance, product mechanism, proof cue, and action;
- one dominant product stage using a real screenshot, artifact, output, or an
  explicitly conceptual representation;
- one real CTA destination or an explicitly labeled availability state;
- public claims mapped to evidence IDs; unknowns remain internal;
- exact HTML/SVG text for product name, claims, dates, prices, Logo, and CTA;
- text-free generated imagery only when it improves the product story;
- editable `onepage.html`, high-resolution `onepage.png`, `source.md`,
  `brief.md`, `content.md`, `project.json`, prompt record, and `audit.json`;
- a recorded human review at original size and thumbnail size.

Reject generic three-card layouts, unsupported superlatives, fake product UI,
decorative prompt boxes, dead CTA buttons, synthetic testimonials, baked-in
critical text, and output accepted only because it renders.

## Read before authoring

Read all four references:

1. `references/content-system.md` — truth ledger, Brand Spine, headline spine,
   proof, and conversion.
2. `references/layouts.md` — semantic OnePage layouts and DOM contracts.
3. `references/art-direction.md` — visual systems, product staging, and hybrid
   image-generation policy.
4. `references/quality-gate.md` — machine and human release criteria.

Read `references/config.md` when brand, output, aspect, or persistent preferences
need resolution.

## Workflow

### 1. Preserve and classify source truth

When the user says “以上内容” or “当前结果”, use the current conversation. Save
the exact relevant input as `source.md`; do not request another paste.

Classify every input as:

- `internal context` — planning details, private anecdotes, competitor notes;
- `publishable claim` — product-relevant copy supported by current truth;
- `verified proof` — real UI, artifact, case, metric, source, availability;
- `open evidence` — desired claim awaiting proof.

Keep internal context and open evidence out of visible poster copy.

### 2. Build the product brief

Create `brief.md` before visual code. Record:

- audience tension and viewing moment;
- category, belief, promise, mechanism, difference, boundary, and action;
- one brand thesis that should remain after five seconds;
- one protagonist: product, outcome, artifact, creator, or customer;
- one primary CTA and its immediate next state;
- claim/evidence ledger with source IDs, dates, units, and caveats;
- deliberate omissions needed to keep one argument.

Use `references/content-system.md`. Never turn unsupported adjectives into
numbers, rankings, customers, awards, or traction.

### 3. Compose the OnePage story

Write `content.md` with a scan-ready headline spine:

```text
possibility or audience tension
→ what the product enables
→ mechanism shown through product truth
→ proof or meaningful difference
→ one concrete action
```

Keep the smallest number of visible stages. The first reading zone must reveal
category, relevance, product cue, and action together. Repeat the CTA only when
the composition genuinely has a second readiness point; keep language and
destination identical.

### 4. Select one layout × one art direction

Choose layout from the story relationship, then art direction from Brand Spine:

| Story job | Layout |
|---|---|
| New product or major release | `launch-story` |
| Costly before-state to better after-state | `problem-solution` |
| Product behavior is the differentiator | `product-tour` |
| Trust and outcomes drive adoption | `proof-led` |
| A real alternative or before/after decision | `comparison` |
| Dated launch, event, or limited campaign | `event-launch` |

Use one focused user-choice prompt only when two materially different routes
remain plausible. Honor explicit layout, style, aspect, brand, and direct-run
choices without asking them again.

### 5. Resolve brand and product assets

Use this order:

1. explicit task paths or `--brand-profile`;
2. target repository brand system and real assets;
3. `SKILL_PRODUCT_ONEPAGE_BRAND_PROFILE`;
4. `SKILL_PROFILE_PATH` or shared profile;
5. packaged Skill Publisher default.

Prefer real screenshots, covers, outputs, packaging, or interface states. Show
them large enough to understand. Record source, truth status, crop, alt text,
and fallback for every asset.

### 6. Generate supporting imagery only when useful

Use the strongest configured image-generation tool for a text-free hero object,
scene, material, or conceptual metaphor. Save the complete prompt to
`prompts/hero-visual.md` before generation.

Require: no words, letters, numbers, charts, UI, logos, signatures, or
watermarks; declared palette; clean negative space for code-rendered copy; crop
safe for the selected aspect. Keep all factual labels in HTML/SVG.

### 7. Scaffold the project

```bash
python3 "$SKILL_DIR/scripts/onepage_cli.py" scaffold \
  --title "<product promise or launch idea>" \
  --tagline "<category + mechanism + relevance>" \
  --cta-label "<concrete next action>" \
  --cta-url "<real destination>" \
  --source "<source path>" \
  --layout launch-story \
  --style editorial-tech \
  --aspect 4:5 \
  --output-dir "<project directory>" \
  --brand-profile "<brand.json>"
```

Add repeated `--feature "Title|Explanation"` and
`--proof "Claim|Evidence detail|S1"` flags when the source already provides
them. The scaffold is a semantic starting point. Rewrite placeholder geometry
and copy to serve the real product while preserving audit attributes.

### 8. Author the fixed canvas

Use HTML/CSS/SVG. Keep these rules:

- one `<main class="onepage">` fixed canvas;
- header/brand at 4%–10% of area;
- headline plus orientation at 16%–30%;
- product stage at 35%–58%;
- proof and action at 12%–25%;
- one signature motif used two or three times;
- two to four supporting features, separated by alignment and rules before
  containers;
- proof adjacent to the claim it supports;
- source, caveat, and attribution readable but subordinate;
- no external CDN dependency in the final artifact.

Preserve the contracts in `references/layouts.md` so the audit can inspect the
story, proof, product stage, CTA, and asset truth status.

### 9. Render and run the machine gate

```bash
python3 "$SKILL_DIR/scripts/onepage_cli.py" render \
  --input "<project>/onepage.html" \
  --output "<project>/onepage.png" \
  --scale 2

python3 "$SKILL_DIR/scripts/onepage_cli.py" audit \
  --input "<project>/onepage.html" \
  --image "<project>/onepage.png" \
  --report "<project>/audit.json"
```

Fix source, narrative, asset, and geometry causes. A PNG and a high automatic
score are intermediate evidence, not the completion condition.

### 10. Inspect the rendered poster

Review at original detail and thumbnail size:

1. Can a reader name the product category, promise, and next action in five
   seconds?
2. Is one product or outcome clearly the protagonist?
3. Do headings alone form a product story?
4. Does the product stage show real behavior or state its conceptual status?
5. Are claims supported beside the relevant proof?
6. Is critical copy exact, readable, and independent from image pixels?
7. Does the composition remain distinctive after blurring details?
8. Would replacing the Logo with a competitor create a visible contradiction?

Record concrete evidence and run the release gate:

```bash
python3 "$SKILL_DIR/scripts/onepage_cli.py" audit \
  --input "<project>/onepage.html" \
  --image "<project>/onepage.png" \
  --report "<project>/audit.json" \
  --human-review passed \
  --review-note "<what was verified at original and thumbnail sizes>" \
  --strict
```

### 11. Recompose derivatives

Use each derivative's viewing moment:

- `9:16`: mobile story, larger headline, shorter proof, safe CTA zone;
- `1:1`: feed summary, fewer stages, stronger product crop;
- `16:9`: launch banner or presentation, horizontal product stage;
- `A4`: print reading distance, print-safe margins, URL/QR and source line.

Each derivative gets its own HTML master and strict review. Shared copy and
tokens may be reused; geometry may not be inherited by cropping.

### 12. Deliver

Return clickable paths to:

- `onepage.png`
- `onepage.html`
- `brief.md`
- `content.md`
- `audit.json`
- `source.md`
- `prompts/hero-visual.md`

State layout, style, aspect, CTA destination, authentic versus generated
assets, score, human-review result, assumptions, and omitted material.

## CLI

```bash
python3 "$SKILL_DIR/scripts/onepage_cli.py" --help
python3 "$SKILL_DIR/scripts/onepage_cli.py" init-brand --help
python3 "$SKILL_DIR/scripts/onepage_cli.py" scaffold --help
python3 "$SKILL_DIR/scripts/onepage_cli.py" render --help
python3 "$SKILL_DIR/scripts/onepage_cli.py" audit --help
```

Rendering and browser audit use Python 3.9+, Playwright 1.45+, and Chromium.

## Runtime context (shared)

运行前读取本 Skill 包的 `skill.yaml`，由宿主提供 `skill-runtime/v1` 上下文。字段解析顺序为：当前请求、项目上下文、个人 Preferences、品牌 Profile、通用默认值。

- 只使用 Manifest 声明的字段；Profile 保存公开品牌事实，Preferences 保存个人工作偏好。
- `required: true` 字段缺失时，按 Manifest 的问题配置向用户提出一个聚焦问题；用户明确同意后再保存回答。
- 报错提供可复制的 `context_id`、字段路径与来源，诊断内容避开秘密、完整私人路径和原始配置。
