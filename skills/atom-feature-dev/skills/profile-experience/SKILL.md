---
name: lov-atom-profile-experience
description: >
  用共享参数 schema 构建前端配置与 Profile Preset 体验，预填复杂参数并减少 Agent 追问，同时保留显式覆盖和来源可见性。触发：“做 Profile 配置界面”或 “build a preset-driven feature UI”。
license: MIT
compatibility: "Portable Agent Skills format. Adapts to the target application's frontend stack and shared user-profile contract."
depends_on:
  - lov-branding-consistency
metadata:
  author: LovStudio
  version: "0.1.1"
  card_standard: lovstudio/skill-card/v1
  content_class: microcopy
  tags:
    - atom-feature
    - profile
    - preset
    - frontend
    - ux
---

# 功能参数配置 · Feature Presets

让用户在前端一次确定复杂偏好，之后由 UI、CLI、API 和 Agent Skill 共享。Preset 是参数
默认值，不是不可见的永久覆盖；用户总能看到来源并在本次调用显式改写。

## Triggers

### Activate when

- “给这个 feature 做 Profile Preset 配置界面。”
- “让 Agent 优先使用用户预设，少问几次问题。”
- “Build a preset-driven feature UI from the shared schema.”

### Do not activate when

- 只需通用 Agent 聊天 UI 或整套新 App shell；使用对应 App / Agent UI 能力。

## Workflow (MANDATORY)

1. 读取 contract 与 profile schema、目标组件库、真实数据源和品牌上下文。
2. 只为值得跨调用保留的参数提供 Preset；临时输入、秘密和一次性文件不得持久化。
3. 表单字段、校验、枚举、帮助文本和默认值从共享 schema 派生；不复制业务规则。
4. 解析顺序为当前显式值、项目上下文、所选 Preset、共享用户默认、安全默认、最后询问。
5. UI 显示值的来源、修改影响、保存范围、验证错误和恢复方式；支持预览与取消。
6. Agent surface 在调用前读取相同 resolved parameters，只询问仍缺失的结果关键字段。
7. 验证 Preset 命中、显式覆盖、无 Preset fallback、无效迁移和跨 session 回读。

## Copy Gate

前端文案只解释用户要决定什么、当前值来自哪里、保存会影响什么。不得把 schema、组件、
Prompt 或 Agent 内部步骤暴露给普通用户；错误提示给出原因、影响和可执行下一步。

## Output Contract

返回 route/component、Preset schema 与存储 adapter、解析函数、微文案验收和真实交互证据。

## Dependencies

目标项目 UI 栈、共享 Profile 存储和 Core SDK 参数校验器。

