---
name: lov-harness-issue
description: >
  从用户角度深度、全面思考接下来的产品需求。Use when the user reports a product issue,
  bug, vague improvement request, confusing workflow, UX friction, or partial feature
  idea and Codex should harness the issue into underlying user goals, adjacent
  requirements, acceptance criteria, and a bounded execution plan before coding.
depends_on:
  - lov-branding-consistency
---

# 需求解题师 · Product Problem Solver

把用户提交的局部问题转化为可执行的产品需求判断。重点不是扩大改动范围，而是站在真实用户视角，把“用户想完成什么、为什么当前体验不符合预期、接下来最该补齐什么”想清楚。

## Core Rule

先理解用户目标，再决定实现范围。不要只消除报错或按字面修一个点；也不要借机重做整个产品。每次都把需求分层，明确哪些属于本次必须完成、哪些可以顺手补齐、哪些只作为后续建议。

## Workflow

1. **Restate the user goal**
   - 将用户的问题改写成用户正在尝试完成的任务。
   - 区分表层症状、真实目标、产品预期。
   - 如果缺少关键信息，优先从代码、界面、文案、测试和现有产品结构中推断；只有无法安全推断时才询问用户。

2. **Map the current product path**
   - 找到用户进入该问题的路径：入口、操作步骤、数据状态、成功出口。
   - 检查相邻状态：loading、empty、error、success、permission、offline、mobile、long content、invalid input。
   - 对前端产品，实际运行页面或用浏览器/截图验证关键路径；不要只读代码猜测体验。

3. **Infer hidden requirements**
   - 从用户视角列出当前问题背后的隐含需求。
   - 覆盖功能、交互、视觉层级、文案反馈、数据一致性、权限、性能感知、可恢复性。
   - 标注每个需求的证据来源：用户原话、现有代码、产品惯例、验证结果或合理推断。

4. **Set the execution boundary**
   - **Must fix now**: 不完成就无法满足用户当前目标。
   - **Should include now**: 与当前改动同路径、低风险、能明显补齐体验。
   - **Follow-up**: 有价值但会扩大范围、需要产品决策或需要额外数据。
   - **Out of scope**: 明确不做，避免无限扩展。

5. **Implement or plan**
   - 如果用户要求执行，直接实施 `Must fix now`，并在风险合理时包含 `Should include now`。
   - 如果用户只要求分析，输出需求拆解和优先级，不改文件。
   - 修改代码时保持范围紧凑，遵循项目既有模式；不要把需求推演变成无关重构。

6. **Verify from the user path**
   - 用用户路径验证，而不只是运行最低层测试。
   - 对 UI/UX 问题，验证桌面和移动端的布局、状态反馈和主要交互。
   - 记录无法验证的部分和原因。

## Output Contract

工作中可以简短说明推断；最终回复应包含：

- **用户目标**: 用户真正想完成的事。
- **本次完成**: 已实施或建议立即实施的需求。
- **顺手补齐**: 同路径中一起处理的体验缺口。
- **后续建议**: 暂缓但值得产品排期的需求。
- **验证结果**: 运行的命令、浏览器验证、截图检查或未验证原因。

如果最终没有代码改动，改用“需求结论、优先级、验收标准、开放问题”的结构。

## Scope Guardrails

- 不要因为发现更多潜在机会就默认全部实现。
- 不要把用户的 bug 当作纯技术错误处理，除非它确实只影响内部构建、依赖或测试。
- 不要为微小问题制造复杂产品方案。
- 不要在没有证据时断言用户意图；将推断标注为推断。
- 如果当前问题涉及高风险数据、支付、权限、安全或生产系统，先收紧范围并说明风险。

## Good Triggers

- “这里不好用，帮我优化一下。”
- “这个 bug 修一下，但要符合产品预期。”
- “用户点这里之后流程不对。”
- “这个页面/功能感觉还没完整。”
- “Based on this issue, think through the next product requirements.”
- “Do not just patch the bug; make the user flow make sense.”

## Runtime context (shared)

运行前读取本 Skill 包的 `skill.yaml`，由宿主提供 `skill-runtime/v1` 上下文。字段解析顺序为：当前请求、项目上下文、个人 Preferences、品牌 Profile、通用默认值。

- 只使用 Manifest 声明的字段；Profile 保存公开品牌事实，Preferences 保存个人工作偏好。
- `required: true` 字段缺失时，按 Manifest 的问题配置向用户提出一个聚焦问题；用户明确同意后再保存回答。
- 报错提供可复制的 `context_id`、字段路径与来源，诊断内容避开秘密、完整私人路径和原始配置。
