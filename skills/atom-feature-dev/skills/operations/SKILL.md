---
name: lov-atom-operations
description: >
  为原子功能补齐适用的文档、测试、SEO、GEO、用户系统、支付、分析与支持闭环，并对不适用项记录理由。触发：“把 feature 做到可运营”或 “complete atom feature operations”。
license: MIT
compatibility: "Portable Agent Skills format. Reuses the target project's documentation, test, auth, billing and analytics stack."
depends_on:
  - lov-branding-consistency
metadata:
  author: LovStudio
  version: "0.1.1"
  card_standard: lovstudio/skill-card/v1
  content_class: authored-prose
  tags:
    - atom-feature
    - documentation
    - testing
    - seo
    - geo
    - auth
    - payment
---

# 功能运营 · Feature Operations

把实现完成的 atom 变成可理解、可验证、可发现、可授权、可售卖和可维护的功能。每一项先
做适用性判断，不用“全都有”制造空集成。

## Triggers

### Activate when

- “把这个 feature 的文档、测试、SEO、GEO、用户和支付一起补齐。”
- “检查哪些运营能力适用，哪些应该明确不做。”
- “Build and complete atom feature operations with evidence.”

### Do not activate when

- 只需外部发布、商店提交或修改共享权限；需要独立授权和发布能力。

## Authorship Integrity

公开文档与发现内容属于 authored prose。写作前读取
`references/authorship-integrity.md`，只使用已验证的能力、限制、案例和结果；不虚构用户、
指标、排名、收入、评价或第一手经历。

## Workflow (MANDATORY)

1. 读取 manifest、contract、真实实现和验证证据，建立可公开事实账本。
2. Docs 默认适用：写 quickstart、参数、示例、错误、迁移、隐私和 surface 差异。
3. Tests 默认适用：unit、contract、integration、E2E 和跨 surface vector 按风险选择。
4. SEO/GEO 仅用于公开页面或文档：唯一 URL、metadata、结构化数据、可引用答案和真实证据。
5. Auth 仅在身份、权限、同步或配额需要时接入；秘密留在后端，权限在服务边界验证。
6. Payment 仅在真实售卖、订阅或计量存在时接入；价格、扣费、退款与 entitlement 可回读。
7. Analytics 只记录完成任务所需的最小事件；定义漏斗、失败原因、成本和隐私边界。
8. 每项写入 artifact、状态和 evidence；不适用项写理由，发布状态由对应渠道回读。

## Output Contract

返回 Operations 矩阵、完成的制品与验证、公开内容事实来源和剩余阻塞。文档生成或 API 成功
不能替代线上可发现、真实登录、真实扣费或渠道上线证据。

## Dependencies

目标项目现有文档、测试、Auth、支付与分析设施；不强制指定供应商。
