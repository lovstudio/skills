# Changelog

## [0.1.1] - 2026-09-07

### Added

- 统一展示名为「网关工坊」，保持调用 ID 与能力契约。

## 0.1.0

- 初始 Skill Kit：`lov-api-creator`，在 uni-api 后端为 app 创建网关端点并接入 /docs 分组，
  在 uni-app 前端封装统一调用层。
- 模块：`lov-backend`（网关端点创建）、`lov-frontend`（调用层封装）。
- 流水线：`full`（backend → frontend）、`backend`、`frontend`。
- 接入 `user-profile/v1` 契约，附 skill-card / cases / pricing 信任记录与分组分析。
