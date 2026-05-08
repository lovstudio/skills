# Changelog

All notable changes to this skill are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) · Versioning: [SemVer](https://semver.org/)

## [1.3.4] - 2026-05-08

### Added

- Obsidian callout rendering for `> [!NOTE]`, tips, warnings, quotes, and related callout types.
- Emoji fallback rendering using cached Twemoji images when available, with local emoji-font fallback.
- LaTeX-style formula handling for inline `$...$` and display `$$...$$` / `\[...\]`; `matplotlib` is optional for rendered formula images.
- YAML-style frontmatter support for document options such as title, author, theme, watermark, cover, TOC, and watermark settings. Explicit CLI arguments take precedence.
- Broader Linux font discovery and built-in PDF font fallbacks for lean environments.

### Fixed

- H5/H6 headings are now consumed as compact subsections instead of falling through parser edge cases.
- Code blocks preserve mid-line alignment by escaping all spaces, not only leading indentation.
- Cover-page de-duplication no longer drops body content that appears under the first H1.
- Full/top-band headers use a stable document title instead of page-lagged chapter state.

## [1.3.2] - 2026-04-20

### Changed

- Watermark defaults: single centered mark per page at 0.1 opacity, auto-sized so text width ≈ half page width (previously a tiled grid at theme-dependent opacity with fixed font size 52). Override with `--wm-size / --wm-opacity / --wm-spacing-x / --wm-spacing-y` as before.
- Back cover banner defaults to the bundled `assets/backcover-banner.jpg` (手工川 brand banner). Pass `--banner none` to disable, or `--banner <path>` to use your own.

### Added

- `assets/backcover-banner.jpg` — bundled 手工川 branding banner so the default works for any user who clones the repo.
- `.github/workflows/auto-tag.yml` — on push to `main`, CI auto-bumps the patch version in SKILL.md, tags it, and pushes the tag (which triggers the existing `release.yml`).

## [1.3.1] - 2026-04-20

### Fixed

- Watermark: when `--wm-spacing-x` and `--wm-spacing-y` are both ≥ 2000, render a single horizontally + vertically centered watermark (with baseline compensation) instead of tiling. Enables large single-mark watermarks (e.g. `--wm-size 200 --wm-spacing-x 9999 --wm-spacing-y 9999`).

## [1.3.0] - 2026-04-20

### Added

- New theme `consulting-navy` — McKinsey / BCG / Deloitte deep-research-report aesthetic: navy hero cover block, ALL-CAPS section banners with thick left bar, left page-stripe, white canvas + serif body
- New `cover_style: consulting-block` — solid navy hero with white title + meta column strip (MODE / SOURCES / CONFIDENCE / DATE)
- New `heading_decoration: banner` — H2 renders as tinted box with thick accent left bar (inline, no page break)
- New `SectionBanner` flowable supporting CJK + Latin in section titles
- Theme picker option `l) 咨询深蓝` and pandoc preset row for the new theme

### Fixed

- `_preprocess_md` now strips full leading YAML frontmatter (`--- ... ---`); previously only `title:`/`subtitle:`/`author:`/`date:` lines were filtered, so fields like `mode:` / `tagline:` leaked into the body as prose

## [1.2.0] - 2026-04-13

### Added

- Add latex-clean as official theme option (k) using pandoc+XeLaTeX engine
- New theme: latex-clean — pure LaTeX typography, no cover/decoration, clean academic style
- Pandoc is now a first-class engine choice, not just a fallback

## [1.1.1] - 2026-04-13

### Fixed

- Expand pandoc theme presets from link-color-only to full parameter sets
- Add complete pandoc -V flags table for 7 themes (linkcolor, toccolor, urlcolor, watermark)
- Add chinese-red full working example from 一滕 project

## [1.1.0] - 2026-04-13

### Added

- Add pandoc + XeLaTeX fallback engine for complex documents
- Document pandoc fallback with watermark, headers/footers, and theme-specific link colors
- Fallback triggered when reportlab hangs on wide/complex tables
- Updated skill description to mention dual-engine support

## [1.0.1] - 2026-04-10

### Fixed

- fix silent image drops: resolve relative paths against input md dir
- resolve relative image paths against the input markdown's directory (not cwd)
- warn on missing images instead of silently dropping them (stderr)
- collapse multi-line image refs in _preprocess_md so pandoc --wrap=auto output parses correctly
- SKILL.md: add Input Format section (markdown-only), document pandoc --wrap=none tip
- README.md: add version badge
