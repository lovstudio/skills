# Changelog

## [0.2.1] - 2026-09-07

### Added

- 统一展示名为「公众号草稿操作（旧入口）」，保持调用 ID 与能力契约。

## 0.2.0 - 2026-08-31

- 停止作为公开入口，已有草稿操作路由到 `lov-publish-wechat-article` 的 `existing-draft` 管线。
- 状态契约与差异验证脚本已迁入 Publisher。

## 0.1.0

- Add the public WeChat article read/edit/save/verify workflow.
- Add the portable article-state contract and ego lite adapter guidance.
- Add deterministic before/after state verification.
