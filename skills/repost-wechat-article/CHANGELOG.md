# Changelog

## [0.2.1] - 2026-09-07

### Added

- 统一展示名为「文章转载（旧入口）」，保持调用 ID 与能力契约。

## 0.2.0 - 2026-08-31

- 停止作为公开入口，所有新任务路由到 `lov-article-creator` 的 `repost` 管线。
- 来源保真规则、审计脚本与测试已迁入 Creator。

## 0.1.0

- Added a source-faithful WeChat repost workflow with explicit reprint rights,
  private-context isolation, editorial overlay, and draft-versus-published states.
- Added deterministic local/remote source-block auditing and duplicate-draft
  prevention after `draft/add` returns a media ID.
- Added the verified S创上海 2026 draft case, Skill Card, pricing boundary, and
  local installation metadata.
