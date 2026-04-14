# lovstudio:tech-book

![Version](https://img.shields.io/badge/version-0.1.0-CC785C)
![License](https://img.shields.io/badge/license-Commercial-red)

Write O'Reilly-style technical books chapter by chapter, with a GitHub repo as the single source of truth. Solves LLM context window limitations through a compressed book summary strategy.

Part of [lovstudio/skills](https://github.com/lovstudio/skills) — by [lovstudio.ai](https://lovstudio.ai)

## What It Does

```
┌─────────────────────────────────────────────────────────┐
│  Phase 1: Plan                                          │
│  Collect book info → Generate outline → Create repo     │
├─────────────────────────────────────────────────────────┤
│  Phase 2: Research (per chapter)                        │
│  WebSearch + context7 → refs.md per chapter             │
├─────────────────────────────────────────────────────────┤
│  Phase 3: Write (per chapter, one session each)         │
│  Load OUTLINE + BOOK_SUMMARY + refs + glossary          │
│  Write section by section → Update summary → Push       │
├─────────────────────────────────────────────────────────┤
│  Phase 4: Review                                        │
│  Consistency · Terms · Cross-references · Polish        │
├─────────────────────────────────────────────────────────┤
│  Phase 5: Build                                         │
│  mdBook → HTML  |  Pandoc → PDF (CJK-ready)            │
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

## Get the Full Version

This is a **commercial skill**. The free preview shows what it does; the full version includes the complete 5-phase workflow with detailed prompts and automation.

### Contact

- **WeChat**: `handcraft-chuaner`
- **Email**: `mark@lovstudio.ai`
- **GitHub**: [lovstudio](https://github.com/lovstudio)

After purchase, you'll be added as a collaborator to the private repo containing the full SKILL.md.

## Dependencies

```bash
cargo install mdbook    # or: brew install mdbook
brew install pandoc basictex
brew install gh
```

## License

Commercial — All rights reserved. Contact [lovstudio](https://lovstudio.ai) for licensing.
