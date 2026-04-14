# lovstudio:tech-book

![Version](https://img.shields.io/badge/version-0.1.0-CC785C)

Write O'Reilly-style technical books chapter by chapter, with a GitHub repo as the single source of truth. Solves LLM context window limitations through a compressed book summary strategy.

Part of [lovstudio/skills](https://github.com/lovstudio/skills) — by [lovstudio.ai](https://lovstudio.ai)

## Install

```bash
npx skills add lovstudio/skills --skill lovstudio:tech-book
```

Requires: `mdbook`, `pandoc`, `basictex`, `gh` CLI

## How It Works

```
┌─────────────────────────────────────────────────────────┐
│  Phase 1: Plan                                          │
│  ┌──────────┐   ┌──────────┐   ┌──────────────────┐    │
│  │ Collect   │──▶│ Generate │──▶│ Create GitHub     │   │
│  │ book info │   │ outline  │   │ repo + skeleton   │   │
│  └──────────┘   └──────────┘   └──────────────────┘    │
├─────────────────────────────────────────────────────────┤
│  Phase 2: Research (per chapter)                        │
│  ┌──────────┐   ┌──────────┐   ┌──────────────────┐    │
│  │ WebSearch│──▶│ context7 │──▶│ refs.md per       │   │
│  │ arxiv    │   │ lib docs │   │ chapter           │   │
│  └──────────┘   └──────────┘   └──────────────────┘    │
├─────────────────────────────────────────────────────────┤
│  Phase 3: Write (per chapter, one session each)         │
│  ┌────────────────────────────────────────────────┐     │
│  │ Load: OUTLINE + BOOK_SUMMARY + refs + glossary │     │
│  │ Write: section by section                      │     │
│  │ Update: BOOK_SUMMARY + glossary                │     │
│  │ Commit + push                                  │     │
│  └────────────────────────────────────────────────┘     │
├─────────────────────────────────────────────────────────┤
│  Phase 5: Build                                         │
│  ┌──────────┐   ┌──────────┐                            │
│  │ mdBook   │   │ Pandoc   │                            │
│  │ → HTML   │   │ → PDF    │                            │
│  └──────────┘   └──────────┘                            │
└─────────────────────────────────────────────────────────┘
```

## Context Window Strategy

The key innovation: instead of loading the entire book each session, we maintain:

| File | Size | Purpose |
|------|------|---------|
| `OUTLINE.md` | ~2KB | Full book structure, always loaded |
| `BOOK_SUMMARY.md` | ~5KB | ≤500 words per chapter summary, always loaded |
| `chapter-xx/refs.md` | ~1KB | Current chapter references only |
| `glossary.md` | ~1KB | Term consistency |

**Total context overhead: ~9KB** — leaving most of the window for actual writing.

## Output Formats

- **mdBook HTML** — browsable book site, deployable to GitHub Pages
- **Pandoc PDF** — printable PDF with CJK support (PingFang SC)
- **Raw Markdown** — readable directly on GitHub

## Usage

```
/lovstudio:tech-book                      # Start a new book project
/lovstudio:tech-book write chapter 3      # Write a specific chapter
/lovstudio:tech-book research chapter 5   # Research refs for a chapter
/lovstudio:tech-book review               # Review consistency
/lovstudio:tech-book build                # Build HTML + PDF
```

## License

MIT
