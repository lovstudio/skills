# lovstudio:any2deck

Transform content into professional slide deck images. Creates outlines with style instructions, generates individual slide images, and merges into PPTX/PDF. Supports 16 visual styles, CJK/Latin mixed text, dual-logo branding, and partial regeneration.

Fork of [baoyu-slide-deck](https://github.com/nicepkg/baoyu-slide-deck) with Lovstudio enhancements.

Part of [lovstudio/skills](https://github.com/lovstudio/skills) &mdash; by [lovstudio.ai](https://lovstudio.ai)

## Install

```bash
npx skills add lovstudio/skills --skill lovstudio:any2deck
```

Requires: Image generation skill + Node.js (for PPTX/PDF) + Python 3.8+ (for branding)

## Quick Start

```bash
/lovstudio:any2deck content.md
/lovstudio:any2deck content.md --style bold-editorial
/lovstudio:any2deck content.md --audience executives --slides 12
/lovstudio:any2deck content.md --lang zh
```

## Workflow

```
Content → Analyze → Confirm Style/Audience/Slides
       → Generate Outline → [Review?]
       → Generate Prompts → [Review?]
       → Generate Images → [Apply Branding?]
       → Merge PPTX/PDF → Done
```

## Style Presets

| Preset | Best For |
|--------|----------|
| `blueprint` (default) | Architecture, system design |
| `bold-editorial` | Product launches, keynotes |
| `chalkboard` | Education, tutorials |
| `corporate` | Investor decks, proposals |
| `minimal` | Executive briefings |
| `sketch-notes` | Educational, tutorials |
| `notion` | Product demos, SaaS |
| `watercolor` | Lifestyle, wellness |
| `dark-atmospheric` | Entertainment, gaming |
| `editorial-infographic` | Tech explainers, research |
| `intuition-machine` | Technical docs, academic |
| `scientific` | Biology, chemistry, medical |
| `pixel-art` | Gaming, developer talks |
| `vector-illustration` | Creative, children's content |
| `vintage` | Historical, heritage |
| `fantasy-animation` | Educational storytelling |

Style auto-detected from content signals. Override with `--style <name>`.

## Options

| Option | Description |
|--------|-------------|
| `--style <name>` | Visual style preset or `custom` |
| `--audience <type>` | beginners, intermediate, experts, executives, general |
| `--lang <code>` | Output language (en, zh, ja, etc.) |
| `--slides <N>` | Target slide count (8-25 recommended) |
| `--outline-only` | Generate outline only |
| `--prompts-only` | Generate outline + prompts, skip images |
| `--images-only` | Generate images from existing prompts |
| `--regenerate <N>` | Regenerate specific slide(s): `3` or `2,5,8` |
| `--logo <path>` | Brand logo (top-right, skips cover/back-cover) |
| `--logo2 <path>` | Secondary logo (left of primary) |
| `--presentation` | Strip narration, keep only visual anchors |

## Output Structure

```
slide-deck/{topic-slug}/
├── source-{slug}.md
├── outline.md
├── prompts/
│   ├── 01-slide-cover.md
│   ├── 02-slide-{slug}.md
│   └── ...
├── 01-slide-cover.png
├── 02-slide-{slug}.png
├── ...
├── {topic-slug}.pptx
└── {topic-slug}.pdf
```

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/merge-to-pptx.ts` | Merge slide images into PowerPoint |
| `scripts/merge-to-pdf.ts` | Merge slide images into PDF |
| `scripts/apply-branding.py` | Composite logo(s)/QR onto slides |

## License

MIT
