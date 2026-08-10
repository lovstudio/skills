---
name: lov-professional-infographic
description: >
  Turn the current conversation, a completed answer, Markdown, research, or
  source material into a consulting Exhibit-quality professional infographic
  with an editable HTML/SVG source and high-resolution PNG. Use for
  topic-led public visuals, answer-first executive Exhibits, comparison or heat
  matrices, decision and driver trees, 2x2 positioning maps, waterfalls,
  roadmaps, operating models, and small-multiple data stories. Trigger when the
  user says "把以上内容做成专业信息图",
  "一图总结", "生成咨询风格海报", "咨询 Exhibit", "turn this into a professional
  infographic", or "create a consulting-style visual summary".
license: MIT
metadata:
  author: contributors
  version: "0.3.0"
  tags: infographic consulting exhibit data-visualization html svg png
---

# Professional Infographic

Build an evidence-led consulting Exhibit, not a decorated summary.

Requires Python 3.8+. PNG rendering and browser audit require Playwright for
Python and Chromium. Brand assets and output paths remain user-configurable.

```text
source
→ decision and evidence graph
→ title mode + governing recommendation
→ semantic Exhibit template
→ visible evidence + direct annotation
→ recommendation after evidence
→ code-rendered master
→ technical + semantic gate
→ human visual review
```

Default to a `16:9` master. Treat `4:5`, `1:1`, and `A4` as separately
recomposed derivatives.

## Non-negotiable outcome

Deliver:

- one display title that makes the subject, purpose, or reader job clear;
- one dominant visual relationship that supports a governing conclusion;
- one evidence-backed recommendation after the main visual;
- visible values, units, periods, definitions, caveats, and sources;
- semantic color, position, length, shape, connection, order, or containment;
- direct annotations at decision-changing evidence;
- editable `poster.html` and high-resolution `poster.png`;
- brand Logo at upper-right or lower-right;
- attribution such as `本信息图由 Skill Publisher 的「专业信息图」Skill 生成`;
- `brief.md`, `source.md`, and `audit.json`.

For a standalone executive Exhibit with known context, `action` title mode may
state the conclusion at the top and omit the tail recommendation. Reject generic
card walls, prose tables, unsupported scores, duplicated conclusions, oversized
titles, decorative AI imagery, and any output that merely passes a technical
audit.

## Required references

Read these before authoring:

1. `references/exhibit-benchmark.md`
2. `references/consulting-standard.md`
3. `references/visual-grammar.md`
4. `references/spec-schema.md`

Read `references/hybrid-rendering.md` only if a custom text-free illustration
may materially improve comprehension. Read `references/user-config.md` when
brand or output configuration is unresolved.

## Workflow

### 1. Preserve and scope the source

If the user says “以上内容”, “当前结果”, or similar, use the current conversation
result. Do not ask them to paste it again.

Save exact input as `source.md`. Identify:

- audience and decision/use moment;
- governing conclusion;
- evidence type: qualitative, quantitative, or mixed;
- material gaps that prevent a defensible chart;
- what must be omitted to keep one argument.

Split genuinely separate stories into separate Exhibits.

### 2. Build `brief.md`

Create an evidence graph before visual code:

| ID | Claim / criterion | Exact evidence | Encoding | Annotation |
|---|---|---|---|---|
| C1 | | S1 | position / length / color / connection | |

For every visible mark, record:

- exact source and location;
- unit, denominator, and period;
- fact, estimate, assumption, or interpretation;
- caveat.

Do not invent proxy values. Label qualitative positions and judgments.

### 3. Choose title mode and place the recommendation

Default to `topic` mode for public-facing infographics:

1. Header: explain the subject, purpose, or comparison job.
2. Main visual: present the evidence relationship.
3. Tail: state the recommendation, boundary, or next action.

Use `action` mode only when the audience already knows the subject and expects
an executive Exhibit. Then the title may state subject + directional finding +
implication, and no separate recommendation band should repeat it.

In either mode, avoid empty labels such as “趋势分析” without a reader job. Keep
the recommendation linked to visible evidence and source IDs.

### 4. Select one semantic template

Use `references/visual-grammar.md`.

| Relationship | Template |
|---|---|
| Alternatives × consistent criteria | `comparison-matrix` |
| Sequential constraints | `decision-tree` |
| Result → drivers → subdrivers | `driver-tree` |
| Two independent axes | `positioning-map` |
| Additive value movement | `waterfall` |
| Phases, milestones, gates | `roadmap` |
| Actors, capabilities, flows, outcomes | `operating-model` |
| Repeated comparison on one scale | `small-multiples` |

Use a single user-choice prompt only when two materially different templates
remain plausible. Pre-fill the recommendation, two alternatives, master aspect,
and brand. Do not re-ask explicit choices.

### 5. Resolve brand configuration

Resolution order:

1. explicit `--brand-profile`;
2. `SKILL_PROFESSIONAL_INFOGRAPHIC_BRAND_PROFILE`;
3. `SKILL_PROFILE_PATH`;
4. `brand.profile` in the shared Skill Publisher profile;
5. packaged public Skill Publisher default.

Initialize only when none is usable:

```bash
python3 "$SKILL_DIR/scripts/infographic_cli.py" init-brand \
  --name "Brand Name" \
  --logo "/absolute/path/to/logo.svg" \
  --copyright "Generated by Brand's Professional Infographic Skill"
```

Never hard-code a private workspace path into the public Skill.

### 6. Scaffold the selected Exhibit

```bash
python3 "$SKILL_DIR/scripts/infographic_cli.py" scaffold \
  --title "<subject, purpose, or comparison job>" \
  --title-mode topic \
  --recommendation "<evidence-backed advice>" \
  --source "<source path>" \
  --template comparison-matrix \
  --mode qualitative \
  --aspect 16:9 \
  --output-dir "<project directory>" \
  --brand-profile "<brand.json>"
```

The template is a semantic skeleton, not finished design. Replace every
placeholder. Preserve `data-*` contracts so the audit can inspect the visual
argument.

### 7. Author the Exhibit

Use HTML/CSS/SVG. Apply these rules:

- keep header at 7%–18% of canvas area;
- give the main visual 58%–82%;
- use alignment and rules before containers;
- attach evidence with `data-source-ref`;
- declare visual variables with `data-encoding`;
- mark plotted evidence, annotations, and the decision;
- keep the recommendation after the visual and before the source footer;
- map the recommendation to evidence with `data-source-ref`;
- use a shared scale for comparisons;
- label axes at both ends;
- label branches and outcomes;
- put units beside values;
- make color encode one meaning;
- keep source, caveats, brand, and attribution readable but subordinate.

Do not copy the scaffold text or geometry blindly. The source relationship
determines exact composition.

### 8. Use image generation only as support

Use the hybrid route only for a physical scene, object, or metaphor that cannot
be communicated efficiently with geometry. The generated asset must contain no
text, numbers, charts, logos, watermarks, or pseudo-UI. Keep all facts and labels
in code.

### 9. Render and run the machine gate

```bash
python3 "$SKILL_DIR/scripts/infographic_cli.py" render \
  --input "<project>/poster.html" \
  --output "<project>/poster.png" \
  --scale 2

python3 "$SKILL_DIR/scripts/infographic_cli.py" audit \
  --input "<project>/poster.html" \
  --image "<project>/poster.png" \
  --report "<project>/audit.json"
```

The audit checks:

- template-specific semantic contract;
- title mode, recommendation presence, placement, evidence linkage, and duplication;
- evidence linkage and unit requirements;
- header, visual, footer, and generic-card area;
- data points, annotations, decision markers, and encoding tokens;
- low-occupancy blocks;
- copy, overflow, contrast, images, logo, and PNG dimensions;
- a 100-point machine proxy with an 85 threshold and critical-dimension floors.

The proxy is not proof of professional quality.

### 10. Inspect the rendered image

Open `poster.png` at original detail and at thumbnail size. Review:

1. Can the reader state what the infographic is for after five seconds?
2. Does the reading path move from topic to evidence to recommendation?
3. Is the recommendation visible at the tail and supported by the visual?
4. Does each color, position, length, shape, or connection have a named meaning?
5. Are decisive differences directly annotated?
6. Is there any large empty container or prose disguised as a chart?
7. Are units, axes, branches, zones, source, and caveats explicit?
8. Does it look commissioned rather than template-generated?

Perform deliberate revisions until both the strict gate and visual review pass.
Do not report success because `audit.json` contains zero technical errors.

Record the exact reviewed image and concrete review evidence, then run the
release gate:

```bash
python3 "$SKILL_DIR/scripts/infographic_cli.py" audit \
  --input "<project>/poster.html" \
  --image "<project>/poster.png" \
  --report "<project>/audit.json" \
  --human-review passed \
  --review-note "<what was verified at full size and thumbnail size>" \
  --strict
```

`passed` without both `--image` and a specific review note is invalid.

### 11. Deliver

Return clickable paths to:

- `poster.png`
- `poster.html`
- `brief.md`
- `audit.json`
- `source.md`

State the selected title mode, template, evidence mode, aspect, proxy score, and
human-review result. Disclose assumptions and omitted material.

## CLI

```bash
python3 "$SKILL_DIR/scripts/infographic_cli.py" --help
python3 "$SKILL_DIR/scripts/infographic_cli.py" init-brand --help
python3 "$SKILL_DIR/scripts/infographic_cli.py" scaffold --help
python3 "$SKILL_DIR/scripts/infographic_cli.py" render --help
python3 "$SKILL_DIR/scripts/infographic_cli.py" audit --help
```

Rendering and browser audit require:

```bash
python3 -m pip install "playwright>=1.45,<2"
python3 -m playwright install chromium
```

## Runtime context (shared)

运行前读取本 Skill 包的 `skill.yaml`，由宿主提供 `skill-runtime/v1` 上下文。字段解析顺序为：当前请求、项目上下文、个人 Preferences、品牌 Profile、通用默认值。

- 只使用 Manifest 声明的字段；Profile 保存公开品牌事实，Preferences 保存个人工作偏好。
- `required: true` 字段缺失时，按 Manifest 的问题配置向用户提出一个聚焦问题；用户明确同意后再保存回答。
- 报错提供可复制的 `context_id`、字段路径与来源，诊断内容避开秘密、完整私人路径和原始配置。
