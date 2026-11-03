# Changelog

All notable changes to this skill are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) · Versioning: [SemVer](https://semver.org/)

## [0.2.3] - 2026-11-03

### Fixed

- PDF 文字层不再出现部首码位：Chrome（Skia）把与部首共用字形的汉字写成 U+2F00–U+2FD5、U+2E80–U+2EF3 的码位，复制或搜索「手工川」会得到「⼿⼯川」。导出 PDF 后自动运行新增的 `scripts/fix_pdf_tounicode.py`，按嵌入字体从本机字体 cmap 推对照表，只改写 ToUnicode，页面渲染不变；仍有残留时写入 manifest 的 `warnings`。
- 对照表按字体推，不共用一张 PingFang 表：同一部首在不同字体里对应的汉字不同，单表会把 Noto Sans SC 排的「用户」改成「用戶」、Songti SC 排的「口」改成「又」。

### Added

- `scripts/fix_pdf_tounicode.py` 可单独修复任何 Chrome/Playwright 打印的 PDF，供 deep-research、lov-bp-deck 等 Skill 调用；仍有部首码位时退出码为 1。
- `--self-test` 的样稿加入「手工川：大、一、人、口、户」，核对 PDF 文字层还原为原字。

## [0.2.2] - 2026-09-25

### Added

- 采用规范检出（rich-export-skill）中按 9 月 7 日迁移标准整理的源码，替换 adopt 时从非规范副本带入的旧 manifest 与重复小节

## [0.2.1] - 2026-09-25

### Added

- 合并本地未提交改动到上游 0.2.0 之上
- 本地改动：统一展示名为「富文档导出」，保持调用 ID 与能力契约。

## [0.2.0] - 2026-08-24

### Added

- add the shared feedback-classification and approval-invalidation gate used by every LovStudio Skill
