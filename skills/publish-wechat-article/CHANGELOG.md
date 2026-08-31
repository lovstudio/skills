# Changelog

All notable changes to this skill are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) · Versioning: [SemVer](https://semver.org/)

## [0.8.0] - 2026-08-31

### Added

- 将原 `lov-wechat-article-operator` 的已有草稿读取、最小修改、保存重载与状态差异验证并入 Publisher。
- 新增 `draft_read` 与 `draft_saved` 终态、文章状态契约和 `verify_article_state.py`。

### Changed

- 公众号远端创建、编辑、核验与正式发布统一由一个公开入口负责。

## [0.7.0] - 2026-08-31

### Added

- 发布预检新增研究评测内容交接门与 4:3 正文首图验证。
- 远端写入前拒绝缺少方法、实际 Prompt、评分示例、复现链或独立正文首图的文章。
- 网关发布脚本内置相同门禁，直接调用也不能绕过正文首图与 benchmark 可复现性检查。

## [0.6.0] - 2026-08-31

### Added

- add profile-driven editorial component gates
- validate permanent endcaps and personal profile cards before remote writes
- require active, available campaigns until they are full, closed, paused, or expired

## [0.5.0] - 2026-08-31

### Added

- compose `lov-image-decorator` before Lovpen rendering for article images that need reader-visible Caption
- require explicit Caption text, source-preserving derivatives, receipts, and no duplication with alt or adjacent prose
- document artwork, screenshot, table, diagram, attribution, endorsement, and no-Caption routing

## [0.4.0] - 2026-08-28

### Added

- Require branded cover composition receipts and Lovpen WeChat-copy HTML for normal draft creation
- fail closed before remote writes when either upstream artifact is missing or mismatched
- retain compact Markdown and unverified covers only behind explicit diagnostic flags

## [0.3.1] - 2026-08-27

### Fixed

- route original declarations through the logged-in `operate_appmsg` web API instead of silently ignored public draft fields
- require explicit rights confirmation and post-save reload evidence before reporting an original declaration as verified
- treat public API `digest` as the separately verifiable article recommendation/summary field

## [0.3.0] - 2026-08-27

### Added

- add verified editor-field enrichment
- require original declaration, concise recommendation copy, and branded cover readback before a draft is ready

## [0.2.1] - 2026-08-27

### Fixed

- verify Lovpen styles against the stored WeChat draft
- allow only observed anchor and position sanitization while rejecting other remote layout changes

## [0.2.0] - 2026-08-27

### Added

- preserve Lovpen WeChat copy HTML without style reconstruction
- reject standalone Lovpen documents and verify structure counts plus a normalized full-HTML fingerprint across image URL replacement

## [0.1.2] - 2026-08-27

### Fixed

- validate rendered visible text and UTF-8 HTML bytes against WeChat limits
- keep raw source-size findings as preflight warnings rather than false platform errors

## [0.1.0] - 2026-08-26

### Added

- create and verify WeChat Official Account drafts through the LovStudio gateway
- submit existing drafts for public publication and report terminal platform states
