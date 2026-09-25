# Changelog

## [0.11.1] - 2026-09-07

### Added

- 统一展示名为「文章品牌化（旧入口）」，保持调用 ID 与能力契约。

## 0.11.0 - 2026-08-31

- 停止作为公开入口，品牌化能力路由到 `lov-article-creator` 的 `brand` 管线。
- 正文首图的 canonical 比例由 Creator 统一为 `4:3` 横向，不再沿用本目录历史 `3:4` 规则。

## [0.10.3] - 2026-08-30

### Fixed

- refine artwork and endcap wording
- rename real-artwork sections to 本期封面 and keep product mentions opt-in
- accept and validate top-level `depends_on` declarations in the bundled source validator

## [0.10.2] - 2026-08-29

### Changed

- prefer attributable Public Domain or clearly licensed real artworks for editorial article covers
- replace reader-facing Cover Prompt with an artwork background note when a real artwork is used
- keep the artwork note before the stable brand endcap and record source and rights metadata

## [0.10.1] - 2026-08-27

### Fixed

- resolve publication cover Logo variants
- prefer publication.cover_logo over the generic publication Logo

## [0.10.0] - 2026-08-27

### Added

- add vertical branded opening heroes
- use a 3:4 first body image and suppress duplicate body titles

## [0.9.0] - 2026-08-25

### Added

- Make square WeChat covers place the official publisher Logo at the bottom center by default.
- Preserve the centered wide Logo while deriving the square background before Logo composition.
- Document and validate square Logo sizing, bottom spacing, and safe-area requirements.
- Bump the embedded cover-direction contract to `0.5.2` for the new square bottom Logo safe zone.

## 0.8.0

- Make the `full` branding edition include an independent `4:3` opening hero before the introduction by default.
- Make the sanitized reader-facing cover Prompt section appear after the conclusion and before the stable brand endcap by default.
- Preserve explicit per-article opt-out controls for `opening_hero` and `cover_prompt`.

## 0.7.0

- Align the canonical Skill name, kit name, entrypoint, README commands, and embedded-module compatibility labels to `lov-wechat-article-branding-skill`.
- Treat the published name alignment as the release baseline for channel packaging.

## 0.6.1

- Add the skill-owned `prompts/cover-hero-editorial-painterly.md` production template for artistic-base covers.
- Require `cover-direction` to read the shared template before creating an article-specific cover Prompt instance.
- Keep the reader-visible Prompt option separate from the internal production Prompt while making both traceable inside the branding skill.

## 0.6.0

- Persist the previous cover-creation skill's art direction for branded covers: editorial hero composition, painterly rendering, explicit palette, no generated text, and a center-safe zone for the publisher Logo.
- Add a visual quality gate that rejects generic warm still-life substitutions when the configured cover direction calls for an authored artistic base.

## 0.5.0

- Add a dedicated cover-composition module that restores the established WeChat cover treatment: artistic background, bottom dimming, and the official publisher Logo centered directly on the canvas.
- Derive the square sharing crop from the centered-logo wide composition and keep the composition separate from the optional opening hero.

## 0.4.0

- Separate the publisher/account identity from the studio and product brands through a required `publication` profile.
- Require covers and opening heroes to use the official publisher Logo, with no silent fallback to a studio or product Logo.
- Render only the primary URL for each product in stable endcaps and reject duplicated product links in brand-level link lists.

## 0.3.0

- Add independent `opening_hero` and `cover_prompt` publication options.
- Separate private production prompts from sanitized reader-copyable cover prompts.
- Define default placement, unique markers, and reload acceptance for opening hero and cover prompt blocks.

## 0.2.0

- Add title polishing as a separate content-intelligence step, including publisher voice and interview/reprint handling.
- Keep approved brand endcaps stable and independent from article-specific metaphors or conclusions.
- Extend the quality gate to verify title identity, reprint context, and reusable brand copy.

## 0.1.0

- Add the article-access, content-intelligence, cover-direction, brand-application, and quality-gate modules.
- Add full, content, cover, brand, and audit pipelines.
- Add portable brand-profile configuration and deterministic profile validation.
