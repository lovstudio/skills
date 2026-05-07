---
name: lovstudio-any2deck
category: Document Conversion
tagline: "Content → slide deck images with 16 visual styles, PPTX/PDF export, branding overlay."
description: >
  Generate professional slide deck images from content (Markdown, text, URLs).
  Creates outlines with style instructions, then generates individual slide images.
  Supports 16 visual styles, CJK/Latin mixed text, branding overlays, and
  PPTX/PDF export. Use when the user asks to "create slides", "make a presentation",
  "generate deck", "slide deck", "PPT", "做PPT", "生成幻灯片", "制作演示文稿",
  or wants to turn content into a visual slide deck.
license: MIT
compatibility: >
  Requires an image generation skill (e.g. image-gen) and Node.js for PPTX/PDF merge.
  Python 3.8+ for branding overlay. Cross-platform: macOS, Windows, Linux.
metadata:
  author: lovstudio
  version: "1.0.2"
  tags: slide deck presentation pptx pdf image generation
---

# Slide Deck Generator

Transform content into professional slide deck images.

## Usage

```bash
/lovstudio:any2deck path/to/content.md
/lovstudio:any2deck path/to/content.md --style sketch-notes
/lovstudio:any2deck path/to/content.md --audience executives
/lovstudio:any2deck path/to/content.md --lang zh
/lovstudio:any2deck path/to/content.md --slides 10
/lovstudio:any2deck path/to/content.md --outline-only
/lovstudio:any2deck  # Then paste content
```

## Script Directory

**Agent Execution Instructions**:
1. Determine this SKILL.md file's directory path as `SKILL_DIR`
2. Script path = `${SKILL_DIR}/scripts/<script-name>`

| Script | Purpose |
|--------|---------|
| `scripts/merge-to-pptx.ts` | Merge slides into PowerPoint |
| `scripts/merge-to-pdf.ts` | Merge slides into PDF |
| `scripts/apply-branding.py` | Composite logo(s)/QR onto slides — dual logo, tight-crop, JPG white→alpha (opt-in) |

## Options

| Option | Description |
|--------|-------------|
| `--style <name>` | Visual style: preset name, `custom`, or custom style name |
| `--audience <type>` | Target: beginners, intermediate, experts, executives, general |
| `--lang <code>` | Output language (en, zh, ja, etc.) |
| `--slides <number>` | Target slide count (8-25 recommended, max 30) |
| `--outline-only` | Generate outline only, skip image generation |
| `--prompts-only` | Generate outline + prompts, skip images |
| `--images-only` | Generate images from existing prompts directory |
| `--regenerate <N>` | Regenerate specific slide(s): `--regenerate 3` or `--regenerate 2,5,8` |
| `--logo <path>` | Primary brand logo (top-right, skips cover/back-cover) |
| `--logo2 <path>` | Secondary logo (placed left of primary, optically aligned) |
| `--presentation` | Presentation mode: strips narration text, keeps only visual anchors |

**Slide Count by Content Length**:
| Content | Slides |
|---------|--------|
| < 1000 words | 5-10 |
| 1000-3000 words | 10-18 |
| 3000-5000 words | 15-25 |
| > 5000 words | 20-30 (consider splitting) |

## Style System

### Presets

| Preset | Dimensions | Best For |
|--------|------------|----------|
| `blueprint` (Default) | grid + cool + technical + balanced | Architecture, system design |
| `chalkboard` | organic + warm + handwritten + balanced | Education, tutorials |
| `corporate` | clean + professional + geometric + balanced | Investor decks, proposals |
| `minimal` | clean + neutral + geometric + minimal | Executive briefings |
| `sketch-notes` | organic + warm + handwritten + balanced | Educational, tutorials |
| `watercolor` | organic + warm + humanist + minimal | Lifestyle, wellness |
| `dark-atmospheric` | clean + dark + editorial + balanced | Entertainment, gaming |
| `notion` | clean + neutral + geometric + dense | Product demos, SaaS |
| `bold-editorial` | clean + vibrant + editorial + balanced | Product launches, keynotes |
| `editorial-infographic` | clean + cool + editorial + dense | Tech explainers, research |
| `fantasy-animation` | organic + vibrant + handwritten + minimal | Educational storytelling |
| `intuition-machine` | clean + cool + technical + dense | Technical docs, academic |
| `pixel-art` | pixel + vibrant + technical + balanced | Gaming, developer talks |
| `scientific` | clean + cool + technical + dense | Biology, chemistry, medical |
| `vector-illustration` | clean + vibrant + humanist + balanced | Creative, children's content |
| `vintage` | paper + warm + editorial + balanced | Historical, heritage |

### Style Dimensions

| Dimension | Options | Description |
|-----------|---------|-------------|
| **Texture** | clean, grid, organic, pixel, paper | Visual texture and background treatment |
| **Mood** | professional, warm, cool, vibrant, dark, neutral | Color temperature and palette style |
| **Typography** | geometric, humanist, handwritten, editorial, technical | Headline and body text styling |
| **Density** | minimal, balanced, dense | Information density per slide |

Full specs: `references/dimensions/*.md`

### Auto Style Selection

| Content Signals | Preset |
|-----------------|--------|
| tutorial, learn, education, guide, beginner | `sketch-notes` |
| classroom, teaching, school, chalkboard | `chalkboard` |
| architecture, system, data, analysis, technical | `blueprint` |
| creative, children, kids, cute | `vector-illustration` |
| briefing, academic, research, bilingual | `intuition-machine` |
| executive, minimal, clean, simple | `minimal` |
| saas, product, dashboard, metrics | `notion` |
| investor, quarterly, business, corporate | `corporate` |
| launch, marketing, keynote, magazine | `bold-editorial` |
| entertainment, music, gaming, atmospheric | `dark-atmospheric` |
| explainer, journalism, science communication | `editorial-infographic` |
| story, fantasy, animation, magical | `fantasy-animation` |
| gaming, retro, pixel, developer | `pixel-art` |
| biology, chemistry, medical, scientific | `scientific` |
| history, heritage, vintage, expedition | `vintage` |
| lifestyle, wellness, travel, artistic | `watercolor` |
| Default | `blueprint` |

## Design Philosophy

Decks designed for **reading and sharing**, not live presentation:
- Each slide self-explanatory without verbal commentary
- Logical flow when scrolling
- All necessary context within each slide
- Optimized for social media sharing

See `references/design-guidelines.md` for:
- Audience-specific principles
- Visual hierarchy
- Content density guidelines
- Color and typography selection
- Font recommendations

See `references/layouts.md` for layout options.

## File Management

### Output Directory

```
slide-deck/{topic-slug}/
├── source-{slug}.{ext}
├── outline.md
├── prompts/
│   └── 01-slide-cover.md, 02-slide-{slug}.md, ...
├── 01-slide-cover.png, 02-slide-{slug}.png, ...
├── {topic-slug}.pptx
└── {topic-slug}.pdf
```

**Slug**: Extract topic (2-4 words, kebab-case). Example: "Introduction to Machine Learning" → `intro-machine-learning`

**Conflict Handling**: See Step 1.3 for existing content detection and user options.

## Language Handling

**Detection Priority**:
1. `--lang` flag (explicit)
2. EXTEND.md `language` setting
3. User's conversation language (input language)
4. Source content language

**Rule**: ALL responses use user's preferred language:
- Questions and confirmations
- Progress reports
- Error messages
- Completion summaries

Technical terms (style names, file paths, code) remain in English.

## Workflow

For the full step-by-step workflow, use `references/workflow.md`. Keep the main
flow in this order:

1. Setup & analyze: load `.lovstudio-skills/lovstudio-any2deck/EXTEND.md` when present, save source content, analyze style signals, detect language, choose slide count, and check for existing `slide-deck/{topic-slug}` output before continuing.
2. Confirm: use `AskUserQuestion` for style, audience, slide count, outline review, and prompt review. If custom dimensions are selected, collect texture, mood, typography, and density.
3. Generate outline: read the selected preset from `references/styles/` or combine dimension docs from `references/dimensions/`, then write `outline.md` using `references/outline-template.md`.
4. Review outline when requested, then generate per-slide prompts under `prompts/` using `references/base-prompt.md` and `references/layouts.md`.
5. Review prompts when requested, generate slide images, optionally apply branding with `scripts/apply-branding.py`, then merge PPTX/PDF with the TypeScript scripts.
6. Report the output directory, generated slide count, PPTX/PDF paths, style, audience, language, and any partial failures.

Partial workflows (`--outline-only`, `--prompts-only`, `--images-only`,
`--regenerate`) and slide modification procedures are documented in
`references/workflow.md`.

## References

| File | Content |
|------|---------|
| `references/analysis-framework.md` | Content analysis for presentations |
| `references/outline-template.md` | Outline structure and format |
| `references/modification-guide.md` | Edit, add, delete slide workflows |
| `references/content-rules.md` | Content and style guidelines |
| `references/design-guidelines.md` | Audience, typography, colors, visual elements |
| `references/layouts.md` | Layout options and selection tips |
| `references/base-prompt.md` | Base prompt for image generation |
| `references/dimensions/*.md` | Dimension specifications (texture, mood, typography, density) |
| `references/dimensions/presets.md` | Preset → dimension mapping |
| `references/styles/<style>.md` | Full style specifications (legacy) |
| `references/config/preferences-schema.md` | EXTEND.md structure |

## Notes

- Image generation: 10-30 seconds per slide
- Auto-retry once on generation failure
- Use stylized alternatives for sensitive public figures
- Maintain style consistency via session ID
- **Step 2 confirmation required** - do not skip (style, audience, slides, outline review, prompt review)
- **Step 4 conditional** - only if user requested outline review in Step 2
- **Step 6 conditional** - only if user requested prompt review in Step 2

## Extension Support

Custom configurations via EXTEND.md. See **Step 1.1** for paths and supported options.
