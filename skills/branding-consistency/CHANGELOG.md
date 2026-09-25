# Changelog

## [0.3.1] - 2026-09-07

### Added

- 统一展示名为「品牌审校官」，保持调用 ID 与能力契约。

## 0.3.0

- 新增 `artifact_boundary` 与 `reader_start_state`，明确最终成品默认面对零会话上下文读者。
- 将悬空的“前一版 / 上一稿 / 按你的要求”等协作历史列为 hard failure。
- 为 `copy_audit.py` 增加本次公众号错误的 cold-reader 回归用例。

## 0.2.0

- 更名为 `lov-branding-consistency`，明确其为所有读者可见文本的横切品牌门禁。
- 新增 LovStudio 文本输出 Skill 的显式依赖清单与自动校验。
- 将 `compatibility` 提升为标准顶层字段，并补充英文触发描述。

## 0.1.0

- 创建跨公众号、网站、App、策划案、海报、社交媒体与邮件的语境文案工作流。
- 引入九字段 context contract、可见性防火墙、场景惯例和七遍质量门。
- 新增 Caption 删除测试与 `copy_audit.py` 辅助审计。
- 以公众号艺术首图的真实 Caption 缺陷建立首个案例。
