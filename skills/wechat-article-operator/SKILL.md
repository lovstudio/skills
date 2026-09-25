---
name: lov-wechat-article-operator
description: >
  公众号已有草稿操作的旧兼容入口；不再独立执行或拥有规则，新任务统一路由到 lov-publish-wechat-article 的 existing-draft 管线。Use when, and only when, a legacy task explicitly names this Skill; do not discover for new tasks.
license: MIT
compatibility: "Deprecated compatibility route; requires lov-publish-wechat-article 0.8.0+."
metadata:
  author: contributors
  version: "0.2.1"
  tags:
    - deprecated
    - compatibility-route
  dependencies: []
---

# 公众号草稿操作（旧入口） · WeChat Draft Operator (Legacy)

该 Skill 不再是公开入口，也不再维护独立规则。历史调用必须立即转交给 lov-publish-wechat-article 的 existing-draft 管线，并以目标 Skill 的契约、授权门和验收结果为准。

## Triggers

### Activate when

- 仅当旧任务或旧配置显式调用 lov-wechat-article-operator。
- “读取或修改这篇公众号草稿。”
- The user asks to edit an existing WeChat draft.

### Do not activate when

- 新任务不得通过语义发现本 Skill；直接使用 lov-publish-wechat-article。
- 不读取本目录旧 modules、references 或 scripts 作为新的 canonical 规则源。

## Compatibility handoff

1. 保留用户原始输入、授权范围和目标状态。
2. 路由到 lov-publish-wechat-article 的 existing-draft 管线。
3. 按目标 Skill 重新执行当前版本的预检、状态语义与验收。
4. 最终结果只报告目标 Skill 的真实状态，不把兼容路由写成独立完成。

## Retirement

本目录保留历史实现用于回溯；共享安装与 catalog 不应再暴露本入口。待所有调用方迁移后可单独归档源码。
