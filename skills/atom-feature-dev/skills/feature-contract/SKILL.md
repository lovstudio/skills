---
name: lov-atom-feature-contract
description: >
  把一个用户任务冻结为可版本化的原子 Feature Contract、参数与 Profile Preset schema、错误和真实验收向量。触发：“定义这个 atom 的契约”或 “create an atom feature contract”。
license: MIT
compatibility: "Portable Agent Skills format. Uses the target repository's schema and test conventions."
depends_on:
  - lov-branding-consistency
metadata:
  author: LovStudio
  version: "0.1.1"
  card_standard: lovstudio/skill-card/v1
  content_class: deterministic-output
  tags:
    - atom-feature
    - contract
    - schema
    - acceptance
---

# 功能契约 · Feature Contract

把需求收敛成所有 SDK 与 adapter 共用的唯一业务契约。输出位于目标项目的
`.atom-feature/`，不替代目标语言自己的公开类型。

## Triggers

### Activate when

- “先把这个 atom 的输入、输出、错误和副作用定下来。”
- “为复杂参数设计 Profile Preset，并减少 Agent 后续追问。”
- “Create an atom feature contract and acceptance vectors.”

### Do not activate when

- 只写宽泛产品方案、单个 API 文档或 UI 表单；使用对应能力。

## Workflow (MANDATORY)

1. 读取根 Kit 的 `references/atom-feature-contract.md` 与目标仓库规则、现有类型和测试。
2. 用一句用户结果定义 atom；发现多个独立结果时拆分，不能用页面名代替业务边界。
3. 列出规范化 input、output、错误、权限、副作用、幂等性、并发和版本策略。
4. 为可预设参数生成 `profiles.schema.json`；秘密只允许 locator，不允许值。
5. 记录至少一个来自真实请求的 golden vector，再补参数边界和预期失败。
6. 在 manifest 中把不适用 surface 明确标为 `not-applicable` 并写理由。
7. 用目标语言的 schema/type validator 和根 helper 验证，修改契约后使旧 evidence 失效。

## Output Contract

返回 manifest、contract schema、profile schema、acceptance vectors 的路径，以及仍未冻结的
业务决策。没有真实案例时保持 `planned`，不得制造向量或分数。

## Dependencies

目标项目现有的类型、schema 与测试工具；无外部服务硬依赖。

