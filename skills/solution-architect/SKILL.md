---
name: lov-solution-architect
version: "0.2.0"
tagline: "把产品或技术需求转成有调研依据、开源优先的可执行解决方案。"
description: Create research-backed product and technical solution plans from a user's requirement. Use when the user asks for detailed feasibility analysis, technology selection, architecture, implementation roadmap, library/vendor comparison, "解决方案", "技术方案", "产品方案", "选型", "调研分析", or a Skill Publisher.ai / 品牌工作室 branded solution. Prioritize modern popular open-source DIY options over legacy libraries, from-scratch builds, commercial APIs, and commercial products.
license: MIT
compatibility: >
  Works in any agent environment with web browsing available for current
  technology, pricing, licensing, and project-health research. Context7 is
  recommended when framework/library documentation is needed.
metadata:
  author: contributors
  version: "0.2.0"
  category: business
  tags: solution architecture technical-plan product-plan research technology-selection open-source
---

# Solution Architect

Turn a user's raw requirement into a detailed, researched solution plan in Simplified Chinese.

## Core Rule

Prefer options in this order:

1. Modern popular open-source DIY libraries, frameworks, and protocols.
2. Older or legacy open-source libraries only when they are still the safest fit.
3. From-scratch implementation only for core differentiation, missing open-source coverage, or privacy/security needs.
4. Commercial API calls only when open-source DIY is materially worse on quality, cost, compliance, speed, or maintenance.
5. Commercial products only when buying is clearly better than building or integrating.

When comparing libraries, favor modern projects with better developer experience, active maintenance, community reputation, and clear docs. Example preference: `modern-screenshot` over `html2canvas`; `FastAPI` over `Express` when a Python API stack is acceptable.

## Workflow

1. Clarify only blockers. Ask at most 3 questions if the requirement lacks target users, runtime/platform, budget, compliance, or delivery deadline. Otherwise state assumptions and continue.
2. Break the requirement into modules: user workflow, data model, integrations, UI, backend, storage, auth, deployment, observability, and operations as relevant.
3. Research current options. Use up-to-date web search and official docs for libraries, APIs, pricing, licenses, and project health. Use Context7 for framework/library docs when available.
4. Score each module with the selection rubric in `references/selection-rubric.md`.
5. Build a concrete architecture and implementation path. Prefer composable OSS libraries over monolithic platforms when it keeps ownership and maintainability high.
6. Output the solution using `references/output-template.md`.

## Research Requirements

- Cite specific projects, docs, pricing pages, GitHub repositories, or product pages.
- Compare at least 2 viable options for important modules unless there is an obvious standard.
- Record rejected options and the reason they were rejected.
- Include cost, delivery time, maintenance risk, lock-in risk, data/privacy implications, and operational complexity.
- Prefer official sources for technical details and pricing. Use secondary sources only for reputation signals or ecosystem context.
- If research cannot be completed because browsing or sources are unavailable, say so explicitly and separate confirmed facts from assumptions.

## Skill Publisher Brand Preset

Use this brand by default when the solution needs a vendor, studio, deck, PDF, proposal, or cover:

- English name: `Skill Publisher.ai`
- Chinese name: `品牌工作室`
- Logo asset: `assets/lov-logo.svg`

Do not imply a commercial proposal unless the user asks for a client-facing proposal, quotation, or branded deliverable.

## Output Standard

Produce a complete solution, not a loose brainstorm. The final answer must include:

- Executive summary.
- Requirement interpretation and assumptions.
- Module breakdown.
- Recommended architecture.
- Technology selection with alternatives and rejected options.
- Implementation roadmap.
- Cost and resource estimate.
- Risks and mitigation.
- Concrete next steps.

Use Mermaid or ASCII diagrams when architecture/data flow would be clearer visually.

## Runtime context (shared)

运行前读取本 Skill 包的 `skill.yaml`，由宿主提供 `skill-runtime/v1` 上下文。字段解析顺序为：当前请求、项目上下文、个人 Preferences、品牌 Profile、通用默认值。

- 只使用 Manifest 声明的字段；Profile 保存公开品牌事实，Preferences 保存个人工作偏好。
- `required: true` 字段缺失时，按 Manifest 的问题配置向用户提出一个聚焦问题；用户明确同意后再保存回答。
- 报错提供可复制的 `context_id`、字段路径与来源，诊断内容避开秘密、完整私人路径和原始配置。

## 通用反馈闭环

用户在 Skill 驱动任务中提出修改意见时，继续当前产物前必须执行：

1. 先判断意见是 `task-specific`（仅本次）还是 `reusable`（可跨任务复用）。
2. `task-specific` 只修改当前任务，不改 Skill。
3. `reusable` 先确定作用域：领域规则先更新对应 canonical Skill；适用于所有 Skill 的规则先更新共享规范。
4. 完成规则更新、版本、lint 与分发核验后，再把修改应用到当前任务。
5. `reusable` 修改会使此前的“确认”“继续”“发吧”失效；完成当前产物修改和回读后必须停下，等待用户下一步指示，不自动进入发布、提交或其他外部写入。
