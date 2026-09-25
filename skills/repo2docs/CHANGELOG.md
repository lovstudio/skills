# Changelog

## [0.3.1] - 2026-09-25

### Added

- 合并本地未提交改动到上游 0.3.0 之上
- 本地改动：统一展示名为「文档站工坊」，保持调用 ID 与能力契约。

## [0.3.0] - 2026-08-24

### Added

- add the shared feedback-classification and approval-invalidation gate used by every LovStudio Skill

## 0.2.0

- Generalized from "code repo → docs" to **any folder of source material →
  docs** (code repos, article collections, mixed knowledge folders) — one
  unified flow, no mode switch.
- New **incremental authoring loop**: read one unit at a time, place it in the
  evolving outline, write/refine the page, and refine earlier pages backward.
  Scales past the context window.
- Images are first-class: new `copy_assets.py` copies them into `public/assets/`
  (optional Pillow downscale/transcode of HEIC/TIFF/BMP) and emits a path map for
  inline embedding + galleries.
- New `inventory.py` enumerates and classifies a folder into an ordered manifest
  (overview material first).
- Broadened trigger phrases to cover content/article/knowledge-base folders.

## 0.1.0

- Initial release: code repository → Fumadocs (Next.js) docs site under `/docs`,
  deployed to `{product-id}.example.com/docs` via `lov-deploy-to-vercel`.
