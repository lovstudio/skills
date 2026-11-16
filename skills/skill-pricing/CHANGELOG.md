# Changelog

## [0.3.0] - 2026-11-16

### Changed

- 写入官网会员制：LovStudio 官网的非免费 Skill 一律包含在 VIP 会员全套权益中，不设单项价格、不兑换 Credits（2026-10-21 起）。给官网渠道定价时只判断“免费”还是“计入会员”，卡片不再给建议价、首发价和价格带，目录条目用 `vip_membership`。
- 起因：2026-11-16 上架一个新 Skill 时，按本 Skill 原有流程算出了“139 Credits，一次性购买”并登记到目录与公开定价卡，官网上并不存在单项购买。此前本 Skill 与 Pricing Card 规范都没有提到会员制。
- 其他渠道（如强制法币标价的外部市场）的单项定价流程不变。

## [0.2.2] - 2026-09-07

### Added

- 统一展示名为「Skill 定价师」，保持调用 ID 与能力契约。

## [0.2.1] - 2026-08-26

### Changed

- require Credits-only pricing across LovStudio product surfaces while keeping fiat values inside recharge flows or channel-specific execution records

## [0.2.0] - 2026-08-24

### Added

- add the shared feedback-classification and approval-invalidation gate used by every LovStudio Skill

## 0.1.0

- 新建基于 Skill Pricing Card 的单一指令型定价 Skill。
- 纳入创作者时间成本、维护成本、用户价值、稀缺性、购买信心、生态飞轮、渠道形态和证据缺口。
- 完成本地源码校验与 Agent 安装链接。
