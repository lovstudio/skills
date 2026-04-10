# Changelog

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
