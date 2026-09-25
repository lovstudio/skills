---
name: lov-atom-core-sdk
description: >
  基于已批准的 Atom Feature Contract 实现唯一业务核心与类型化 SDK，让 CLI、API、UI 和 Agent adapter 复用同一规则。触发：“实现共享 SDK”或 “build the atom core SDK”。
license: MIT
compatibility: "Portable Agent Skills format. Reuses the target repository's primary language, package manager, types and tests."
depends_on:
  - lov-branding-consistency
metadata:
  author: LovStudio
  version: "0.1.1"
  card_standard: lovstudio/skill-card/v1
  content_class: deterministic-output
  tags:
    - atom-feature
    - sdk
    - domain-core
    - testing
---

# 功能共享内核 · Feature Core

实现 Feature 的唯一业务真源。SDK 接收规范化参数并返回规范化结果；传输、表单、文案和
Agent 对话不进入核心。

## Triggers

### Activate when

- “按现有 contract 实现这个 feature 的共享 SDK。”
- “把 API 和前端里重复的业务规则收回核心。”
- “Build the atom core SDK and typed public API.”

### Do not activate when

- 只封装现成 SDK 的 CLI、REST 或页面，不修改业务核心。

## Workflow (MANDATORY)

1. 读取 manifest、contract schema、acceptance vectors 和目标仓库真实调用链。
2. 复用项目主语言与包结构；已有核心时增量提取，不创建第二套平行业务层。
3. 定义最小公开 API、类型、稳定错误类别与必要的同步/异步边界。
4. 把业务默认值、校验、排序、计价、状态迁移和副作用协调集中到 SDK。
5. 把网络、CLI argv、HTTP envelope、组件状态、文案和 Profile 存储留给 adapters。
6. 为 golden、参数边界、失败、幂等和副作用回读补聚焦测试。
7. 通过实际包入口从中立目录调用 SDK，记录版本、命令与结果，再标记 `verified`。

## Output Contract

返回 SDK 制品路径、公开符号、输入输出类型、错误映射、测试与真实调用证据。只完成类型检查
或单测时状态最多为 `implemented`。

## Dependencies

目标项目语言运行时、包管理器和测试框架；不强制新增框架。

