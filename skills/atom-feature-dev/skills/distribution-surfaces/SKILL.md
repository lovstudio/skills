---
name: lov-atom-distribution-surfaces
description: >
  从同一 Core SDK 与参数 schema 实现 CLI、REST API 和 Agent Skill adapter，并用相同测试向量验证等价结果。触发：“补齐功能分发形态”或 “build CLI API and Agent surfaces”。
license: MIT
compatibility: "Portable Agent Skills format. Adapts to the target project's CLI, HTTP and Agent runtime conventions."
depends_on:
  - lov-branding-consistency
metadata:
  author: LovStudio
  version: "0.1.1"
  card_standard: lovstudio/skill-card/v1
  content_class: deterministic-output
  tags:
    - atom-feature
    - cli
    - restful-api
    - agent-skill
    - adapters
---

# 功能多端分发 · Feature Distribution

把一个已验证的 SDK 适配为适用的 CLI、REST API 与 Agent Skill。adapter 负责输入翻译、
传输、权限和呈现，不复制业务规则。

## Triggers

### Activate when

- “基于共享 SDK 同时补 CLI、REST API 和 Agent Skill。”
- “检查这些 surface 是否真的行为一致。”
- “Build CLI, API and Agent surfaces for this atom.”

### Do not activate when

- 目标没有已批准的 contract 或可调用核心；先执行 feature-contract 与 core-sdk。

## Workflow (MANDATORY)

1. 从 manifest 选择真正适用的 surface，不为空形态造目录。
2. CLI 使用任务型命令、稳定 JSON envelope、明确退出码、`doctor` 与 `capabilities`。
3. REST API 使用版本化 request/response schema、OpenAPI、认证边界、幂等和结构化错误。
4. Agent Skill/tool schema 复用 contract 字段；先合并 Profile Preset，再只追问结果关键缺失值。
5. 所有 adapter 只调用公开 SDK，不复制校验、默认值或状态迁移。
6. 用同一 acceptance vector 分别调用至少两个 surface，规范化后比较业务结果和副作用。
7. 回读命令、OpenAPI 或工具注册状态；远端发布仍需独立授权与渠道证据。

## Output Contract

返回每个 surface 的入口、artifact、schema、示例、测试命令和验证层级；明确
`implemented`、`verified` 与 `released` 的区别。

## Dependencies

已批准的 Feature Contract 与可调用 Core SDK；其余依赖由目标项目决定。

