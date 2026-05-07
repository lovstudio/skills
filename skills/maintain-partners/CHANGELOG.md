# Changelog

All notable changes to this skill are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) · Versioning: [SemVer](https://semver.org/)

## [0.9.1] - 2026-05-07

### Fixed

- make dependency install paths configurable
- replace fixed runtime skill paths with LOVSTUDIO_SKILLS_INSTALL_DIR
- use python3 -m pip install Pillow in dependency examples

## [0.9.0] - 2026-05-07

### Added

- require explicit partner website config
- remove implicit `$HOME/lovstudio/coding/web` fallback in favor of CLI, `LOVSTUDIO_*` env, or shared profile
- expand `$HOME`-style variables from shared profile paths

## [0.8.0] - 2026-05-07

### Added

- standardize partner env vars on LOVSTUDIO_MAINTAIN_PARTNERS namespace
- use LOVSTUDIO_MAINTAIN_PARTNERS_SITE_ROOT and LOVSTUDIO_MAINTAIN_PARTNERS_FILE as primary variables
- keep older PARTNERS_* and LOVSTUDIO_WEB_ROOT aliases for migration only

## [0.7.0] - 2026-05-07

### Added

- move default profile lookup under ~/.lovstudio
- keep AGENT_SKILL_PROFILE as the portable override
- keep PARTNERS_SITE_ROOT and PARTNERS_FILE as neutral primary runtime variables

## [0.6.0] - 2026-05-07

### Added

- switch partner config API to neutral env names
- use PARTNERS_SITE_ROOT and PARTNERS_FILE as primary variables
- retain LOVSTUDIO_WEB_ROOT and LOVSTUDIO_PARTNERS_FILE as legacy aliases

## [0.5.0] - 2026-05-06

### Added

- add configurable website repo resolution
- support --repo and shared profile JSON
- document portable partner-site initialization
- support configurable partners TSX files, including the current PartnersGrid.tsx location
- add partner category handling for the LovStudio PartnersGrid schema

## [0.4.0] - 2026-05-06

### Changed

- 声明 `depends_on: [lovstudio-find-logo]`，把 logo 发现统一交给 find-logo skill。
- Op 1 改为读取 `~/.lovstudio/logo-collection/<slug>/logo.<ext>`，不再维护独立 homepage scraper。
- README 安装说明补充 `lovstudio-find-logo`，移除 Playwright/SPA scraping fallback。

### Removed

- 删除 `scripts/scrape_logo.py`，避免 maintain-partners 和 find-logo 之间重复维护抓取逻辑。

## [0.3.0] - 2026-04-27

### Added

- Op 5 升级到 retina-ready 工作流：240px 默认 + fixed-box 矩阵 + icon+wordmark 合成
- Op 5 默认 raster 高度从 80 升到 240（3× retina export 密度），强调必须从原图 normalize
- 新增 Op 5 step 3：sed 去除 SVG 内嵌背景 rect，避免 filter 翻成白块盖住图标
- 新增 Op 5 step 4：96×30 fixed-box 矩阵（含边框/圆角）替代 auto-width flex，宽度可预测
- 新增 Op 5 step 6：图标-only SVG → 用 PIL + 品牌字体合成 icon+wordmark PNG
- frontmatter description 扩充：添加 logo 不清晰 / 矩阵格子 / 等宽 box / 图标加文字 等触发短语

## [0.2.0] - 2026-04-27

### Added

- 新增多 logo 等高对齐工作流（Op 5）：file-level 裁切 + 等高 wrap box + 深底统一反白滤镜
- SVG 源文件需先用 rsvg-convert 栅格化再 normalize，否则 viewBox padding 无法裁切
- 深底反白配方：filter: brightness(0) invert(1) opacity(0.88)；已是白色源文件用 .ps-logo-original 跳过反白
- 明确反模式：禁止用 per-logo magic-number CSS height 调整（不稳定、不可维护）
- frontmatter description 扩充触发短语：logo 不一样高 / logo 对齐 / logo 大小不一致 / logo 颜色不统一
