# Changelog

All notable changes to this skill are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) · Versioning: [SemVer](https://semver.org/)

## [0.2.2] - 2026-11-03

### Fixed

- 导出核验新增 PDF 文字层门槛：Chrome/Playwright 从 HTML 打印的 PDF 页面正常，复制或搜索却是部首码位（「⼿⼯川」）。导出后运行 `lov-rich-export` 的 `scripts/fix_pdf_tounicode.py`，输出 `radicals left in text 0` 才算通过，结果记入 `deck-manifest.md`
- 顶层 `depends_on` 加入 `lov-rich-export`，Step 0 一并解析它的安装目录

## [0.2.1] - 2026-11-03

### Fixed

- 导出核验新增硬门槛：PPTX 必须可编辑，文字为原生文本、整页图片为 0；生成器只给整页图片时，按 HTML 版式把 DOM 映射为原生文本框、形状与图片重建 PPTX
- 新增 `scripts/check_pptx_editable.py`，并要求把 PPTX 回读渲染后与源稿逐页比对（Quick Look 只渲染首页，需逐页另存单页 PPTX）

## [0.2.0] - 2026-08-24

### Added

- add the shared feedback-classification and approval-invalidation gate used by every LovStudio Skill
