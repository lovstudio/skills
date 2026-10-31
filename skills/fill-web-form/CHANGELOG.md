# Changelog

## [1.2.2] - 2026-10-31

### Added

- 维护备注：补回 2026-09-03 的 6 条飞书分享表单经验（此前只在未接入真源的安装副本里）
- 维护备注：新增飞书表单登录判断、未登录时编辑器延迟渲染、文本题输入与回读、附件追加上传、附件完成判定、草稿与 resource timing 的核验局限，以及内置浏览器无法上传本地文件

## [1.2.1] - 2026-09-25

### Added

- 合并本地未提交改动到上游 1.2.0 之上
- 本地改动：统一展示名为「网页填表助手」，保持调用 ID 与能力契约。

## [1.2.0] - 2026-08-24

### Added

- add the shared feedback-classification and approval-invalidation gate used by every LovStudio Skill

## [1.1.2] - 2026-05-07

### Fixed

- ask only for missing required web form fields

## [1.1.1] - 2026-05-07

### Fixed

- add release metadata
- add README version badge

## 1.1.0 — 2026-04-14

- Output document now includes "检索文件路径" appendix with tree of all inspected files
- Summary step also displays the inspected files tree for quick review

## 1.0.0 — 2026-04-14

- Initial release: fetch web form → deep-search KB → generate markdown document
