---
name: lov-hanzi-lens
description: >
  Explain one Chinese character through verified pronunciation, Unicode and
  glyph structure, historical lexicography, classical usage, semantic
  relationships, and an evidence-led professional infographic. Use when the
  user asks "解释这个字", "这个字什么意思", "一图讲清这个汉字", "汉字字源信息图",
  "explain this Chinese character", or "Chinese character infographic".
license: MIT
compatibility: >
  Portable Agent Skills format. Requires Python 3.8+, fontTools for deterministic
  glyph-coverage checks, and the lov-professional-infographic dependency.
  User paths, brand assets, and output settings resolve from CLI flags,
  environment variables, or the shared Skill Publisher user profile.
depends_on:
  - lov-professional-infographic
metadata:
  author: contributors
  version: "0.1.0"
  tags: hanzi chinese-character etymology lexicography infographic cjk unicode
---

# Hanzi Lens

Turn one Han character into a source-backed visual explanation. The character
is the subject: do not infer a person's character, fate, relationships, or
identity unless the user explicitly changes the scope.

```text
character
→ Unicode + font coverage
→ source hierarchy
→ fact / commentary / interpretation boundary
→ semantic model
→ professional Exhibit
→ domain + visual release gates
```

## Required references

Read these completely before authoring:

1. `references/research-standard.md`
2. `references/visual-grammar.md`
3. `references/output-contract.md`

Read `references/user-config.md` when brand or output configuration is
unresolved.

The dependency `lov-professional-infographic` is mandatory. Read its
`SKILL.md` and required references before creating or reviewing the Exhibit.

## Non-negotiable outcome

For the standard visual route, deliver:

- a verified reading with region or standard attached;
- Unicode identity and a passing glyph-coverage report;
- form analysis that distinguishes semantic, phonetic, and uncertain parts;
- historical lexicography with exact source labels;
- at least two classical examples in context;
- one governing semantic relationship, not a dictionary card wall;
- an explicit boundary between fact, commentary, interpretation, and visual
  metaphor;
- editable `exhibit/poster.html` and high-resolution
  `exhibit/poster.png`;
- `source.md`, `research.json`, `brief.md`, `font-report.json`,
  `exhibit/audit.json`, and `hanzi-audit.json`;
- full-size and thumbnail human review.

Never invent oracle-bone or bronze forms, turn a modern component mnemonic into
historical etymology, flatten regional readings into one standard, or use
unsupported rarity and auspiciousness scores.

## Workflow

### 0. Resolve context and ask once

Use conversation context to prefill the character, focus, locale, aspect, and
brand. Before running the first generation command, use `AskUserQuestion` once
for the smallest unresolved choice. Recommended defaults:

- scope: character only;
- locale: compare mainland and Taiwan standards when they differ;
- output: explanation + professional infographic;
- aspect: 16:9 master;
- brand: shared user profile.

Do not re-ask options the user already fixed. If the runtime does not expose
`AskUserQuestion`, ask one concise plain-text question.

### 1. Create the research project

```bash
python3 "$SKILL_DIR/scripts/hanzi_lens.py" inspect "翕"

python3 "$SKILL_DIR/scripts/hanzi_lens.py" scaffold "翕" \
  --request "解释「翕」这个汉字" \
  --locale both \
  --output-dir "<project>"
```

The scaffold is intentionally incomplete and non-destructive. Never write into
a non-empty output directory.

### 2. Prove that the glyph can render

Run before visual authoring:

```bash
python3 "$SKILL_DIR/scripts/hanzi_lens.py" font-check "翕" \
  --portable \
  --output "<project>/font-report.json"
```

For Extension B and later ideographs, IVS sequences, or a zero-match result,
select and test an explicit font file. Do not substitute an image of a
different glyph.

### 3. Research by source level

Browse and verify the character. Follow `references/research-standard.md`.
Record exact evidence in `source.md` and structured evidence in
`research.json`.

Required distinctions:

| Layer | Meaning |
|---|---|
| Standard / dictionary fact | Current code point, reading, radical, strokes, recorded sense |
| Historical lexicography | What a named historical dictionary says |
| Commentary | What a named commentator infers from that dictionary |
| Interpretation | A modern synthesis supported by the above |
| Visual metaphor | Geometry used to help comprehension, never presented as paleography |

If sources disagree, show the disagreement. Do not silently choose the most
poetic version.

### 4. Build the semantic model

Complete `research.json` and `brief.md` before visual code.

Choose one governing relationship:

- tension or motion, such as inward ↔ outward;
- root meaning → semantic branches;
- form component → function → recorded use;
- two or more characters × consistent criteria;
- documented chronological form evolution.

Every visible branch, arrow, coordinate, or contrast must map to a source ID.

Run the domain preflight:

```bash
python3 "$SKILL_DIR/scripts/hanzi_lens.py" audit \
  --project "<project>"
```

Warnings about a missing Exhibit are expected at this stage; research errors
must be fixed before continuing.

### 5. Write the action title and scaffold the Exhibit

The title must state a supported finding about the character. Avoid topic
labels such as “认识某字”.

```bash
python3 "$SKILL_DIR/scripts/hanzi_lens.py" exhibit \
  --project "<project>" \
  --title "<source-supported action title>" \
  --template driver-tree \
  --aspect 16:9
```

Template guidance is in `references/visual-grammar.md`. The generated template
is only a semantic skeleton. Replace every placeholder while preserving the
dependency's auditable `data-*` contracts.

### 6. Author for the character, not around it

- Make the target glyph a dominant plotted mark, not a decorative watermark.
- Use form, motion, contrast, or semantic branching as the main visual proof.
- Use code-rendered HTML/CSS/SVG for all text, glyphs, labels, quotes, and
  sources.
- Generated imagery is rarely needed. It must never fabricate ancient forms,
  calligraphy attribution, or pseudo-script.
- Put regional reading differences and scholarly disputes next to the relevant
  mark.
- Keep the brand subordinate.

### 7. Render and inspect

```bash
python3 "$SKILL_DIR/scripts/hanzi_lens.py" render \
  --project "<project>" \
  --scale 2
```

Open `exhibit/poster.png` at original size and at approximately 320 px wide.
Review:

1. Can the reader repeat the governing insight after five seconds?
2. Does the glyph remain the subject?
3. Does the visual prove the title without reading every quote?
4. Can every claim be traced to a source ID?
5. Are fact, commentary, interpretation, and metaphor distinguishable?
6. Are rare glyphs, regional readings, and caveats legible?
7. Is there any generic card wall, fake ancient form, or empty container?

Revise deliberately. A machine pass is not the final judgment.

### 8. Run the strict release gate

```bash
python3 "$SKILL_DIR/scripts/hanzi_lens.py" audit \
  --project "<project>" \
  --human-review passed \
  --review-note "<full-size and thumbnail evidence>" \
  --strict
```

Release only when both the Hanzi domain audit and the delegated professional
infographic audit pass with zero errors and zero warnings.

## CLI reference

```bash
python3 "$SKILL_DIR/scripts/hanzi_lens.py" --help
python3 "$SKILL_DIR/scripts/hanzi_lens.py" inspect --help
python3 "$SKILL_DIR/scripts/hanzi_lens.py" scaffold --help
python3 "$SKILL_DIR/scripts/hanzi_lens.py" font-check --help
python3 "$SKILL_DIR/scripts/hanzi_lens.py" exhibit --help
python3 "$SKILL_DIR/scripts/hanzi_lens.py" render --help
python3 "$SKILL_DIR/scripts/hanzi_lens.py" audit --help
```

## User configuration

Resolution order:

1. explicit CLI flags;
2. `SKILL_HANZI_LENS_*` environment variables;
3. shared `SKILL_SKILLS_*` environment variables;
4. `${SKILL_PROFILE_PATH:-$HOME/.skill-publisher/skills/profile.json}`;
5. safe defaults under `$HOME/Documents`.

Relevant variables:

| Variable | Meaning |
|---|---|
| `SKILL_HANZI_LENS_OUTPUT_DIR` | Hanzi Lens output root |
| `SKILL_HANZI_LENS_INFOGRAPHIC_SKILL_DIR` | Dependency skill directory |
| `SKILL_OUTPUT_DIR` | Shared output root |
| `SKILL_SKILLS_INSTALL_DIR` | Shared skill installation directory |
| `SKILL_PROFILE_PATH` | Shared profile JSON |
| `SKILL_PROFILE_PATH` | Shared brand profile |

Never hard-code a private workspace or brand path into a reusable project.

## Runtime context (shared)

运行前读取本 Skill 包的 `skill.yaml`，由宿主提供 `skill-runtime/v1` 上下文。字段解析顺序为：当前请求、项目上下文、个人 Preferences、品牌 Profile、通用默认值。

- 只使用 Manifest 声明的字段；Profile 保存公开品牌事实，Preferences 保存个人工作偏好。
- `required: true` 字段缺失时，按 Manifest 的问题配置向用户提出一个聚焦问题；用户明确同意后再保存回答。
- 报错提供可复制的 `context_id`、字段路径与来源，诊断内容避开秘密、完整私人路径和原始配置。
