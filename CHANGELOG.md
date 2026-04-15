# Changelog

## 0.7.1

- **tech-book**: New skill — generate complete technical books with mdbook/pandoc, deploy to GitHub Pages
- **md2pdf**: Removed — functionality fully covered by `any2pdf` (reportlab + pandoc fallback)

## 0.7.0

- **skill-optimizer**: Add Step 7 — auto commit & push after optimization (no more manual git push)
- **finder-action**: Fix sandbox entitlements — use `temporary-exception.files.absolute-path.read-write` instead of `files.user-selected.read-write`, document sandbox-must-be-on requirement

## 0.6.0

- **thesis-polish**: New skill — MBA thesis polishing to national outstanding thesis standards
- **finder-action**: New skill — generate Mac Finder right-click menu actions (Quick Action or Finder Sync Extension)
- **pdf2png**: New skill — PDF → single concatenated PNG via macOS CoreGraphics
- **md2pdf**: New skill — Markdown → PDF via pandoc + xelatex with CJK support
- **gh-tidy**: New skill — interactive GitHub repo triage (issues, PRs, stale branches, labels)
- **obsidian-reset-cache**: New skill — reset Obsidian cache to fix "Loading cache..." hang
- **any2pdf**: Add pandoc + XeLaTeX fallback engine, latex-clean theme, watermark params, image-cover mode
- **README**: Auto-generate skills table from SKILL.md frontmatter via CI, shield badges for stats
- **CI**: Add `sync-readme.yml` workflow to keep skills table in sync on push

## 0.5.2

## 0.5.1

- **README**: Reorganize skills into 6 categories (Meta Skills / Document Conversion / Content Processing / Content Creation / xBTI / Dev Tools), add missing `document-illustrator` skill, extract Theme Gallery to `docs/THEME-GALLERY.md` with external links from skill descriptions

## 0.5.0

- **document-illustrator**: New skill (migrated from op7418/Document-illustrator-skill). Redesigned workflow: backup → global insertion planning → parallel image generation → async insert-in-place → cleanup. Uses anchor-text positioning instead of line numbers to handle offset drift. All images generated concurrently via Agent tool. SKILL.md trimmed from 480 to ~120 lines.

## 0.4.1

- **any2pdf**: Fix silent image drops. Relative `![alt](path)` references are now resolved against the input markdown's directory (not cwd), missing images emit a `WARN: image not found` to stderr instead of being silently dropped, and multi-line image refs (caused by pandoc's default `--wrap=auto`) are collapsed during preprocessing. SKILL.md gains an "Input Format" section clarifying markdown-only input and a pandoc `--wrap=none` pipeline tip. Bumps skill version 1.0.0 → 1.0.1.

## 0.4.0

- **skill-optimizer**: New meta skill — audits an existing skill against repo conventions + official skill-creator best practices, applies fixes, bumps semver version, and prepends a per-skill `CHANGELOG.md` entry. Fully automatic, context-driven (prioritizes issues raised in the current conversation). Ships `lint_skill.py` + `bump_version.py` (stdlib only).

## 0.3.2

- **xbti-creator**: Fix step numbering (duplicate Step 2), fix Gallery PR submission (wrong gh fork syntax, missing index.js/case.json/registry updates, image→images dir), add Gallery opt-in to initial questionnaire

## 0.3.1

- **xbti-gallery**: New skill — browse all community-created BTI personality tests at xbti.lovstudio.ai

## 0.3.0

- **anti-wechat-ai-check**: New skill — analyze text for WeChat AI detection vulnerability, provides rewrite suggestions
- **xbti-creator**: New skill — create XBTI format images with structured data
- **image-creator**: Renamed from image-gen for clarity
- Updated CLAUDE.md skills table and root README

## 0.2.0

- **skill-creator**: New skill to scaffold lovstudio skills with proper structure (SKILL.md + README.md + scripts/)
- **any2deck**: Fork of baoyu-slide-deck — content → slide deck images with 16 styles, PPTX/PDF export, branding overlay

## 0.1.1

- Add README.md for fill-form skill
- Update root README with fill-form in skills table
- Require README.md per skill in project conventions (CLAUDE.md)

## 0.1.0

- **any2pdf**: Markdown → styled PDF with CJK/Latin mixed text, 14 color themes, cover pages, TOC, watermarks
- **any2docx**: Markdown → styled DOCX with same theme palette, python-docx based
- **fill-form**: Fill Word form templates (.docx) with table-based field detection and CJK font support
- invest-report theme (楷体+深红) for any2docx
- Theme gallery with 14 preview images
- Skill directories reorganized under `skills/`
- Per-skill README.md with install instructions
