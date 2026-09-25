# Skill Group Composition

## Nearby Skills Inspected

- `lov-solution-architect` 接收宽泛需求并输出研究型技术方案；它不拥有实际代码和跨形态验收。
- `lov-app-generator` 创建或标准化整套 Web、Tauri 或原生 App；它拥有 App shell，不拥有单个
  Feature 在 SDK、CLI、API 与 Agent Skill 间的一致性。
- `lov-cli-creator` 把真实项目后端封装成可安装 CLI，输出稳定 JSON 与 E2E 证据；它可消费
  本 Kit 的 SDK 契约，但不负责其他 surface。
- `lov-api-creator` 面向 uni-api 与 uni-app 的特定网关集成；其后端端点表可作为项目适配器，
  但技术栈和结果边界都比本 Kit 窄。
- `lov-integrate-agent-uiux` 把 Agent transcript、工具状态与输入区接入现有 React 应用；它不
  定义业务参数、Profile Preset 或 Agent Skill 调用契约。
- `lov-init-auth`、`lov-better-seo`、`lov-skill-pricing`、`lov-dev-to-prod` 分别拥有 Auth、SEO、
  Skill 定价和生产制品的单点结果，均为 Operations 或交付阶段的可选下游。
- `lov-skill-creator` 创建可移植 Skill Kit 与信任卡；本 Kit 只为目标 Feature 生成 Agent
  surface 和工具 schema，若要独立发行该 surface，可将其 brief 交给 Creator。

## Atomic Handoffs

1. 可选上游 `lov-solution-architect` 输出已批准的需求与技术约束；本 Kit 从一个可独立验收的
   用户结果开始，并拥有实际实现。
2. 核心 `lov-atom-feature-dev` 接收目标仓库和 Feature brief，输出 `.atom-feature/manifest.json`、
   共享 SDK、适用 adapters、Profile experience、operations 状态、Dashboard 与验证证据。
3. `lov-cli-creator` 可接收 SDK 公共符号、参数 schema 与测试向量，输出安装完成的 CLI；本 Kit
   仍拥有 CLI 与其他 surface 的等价性验收。
4. `lov-app-generator` 或 `lov-integrate-agent-uiux` 可接收 UI route、typed schema 和状态契约，
   输出真实 App shell 或 Agent UI；本 Kit 验收该页面是否使用同一 Feature Contract。
5. `lov-init-auth`、SEO、定价、生产和发布能力只消费 operations brief 或已验证制品；它们拥有
   各自领域的最终状态，本 Kit 只在 Dashboard 回读状态，不代替渠道证据。

## Overlap Decisions

本 Kit 不复制相邻 Skills 的完整脚手架或发布逻辑。它独占三件事：原子 Feature manifest、
跨形态共享业务核心、同一测试向量在多个 surface 上的等价性。相邻 Skills 可以实现某个
adapter，但必须通过明确制品交接，不能成为隐藏依赖。`lov-api-creator` 的 uni-api/uni-app
约束不会被提升为通用默认值；Auth、支付、SEO 与 GEO 只有适用时才进入实现。

## Composition Decision

这是自包含 Skill Kit。六个模块分别产生可独立验收的契约、SDK、分发 adapter、Profile
体验、运营配套和 Dashboard；它们又必须通过同一 manifest 与验收向量组合成一个用户结果。
外部 sibling Skills 均为可选的 artifact-level handoff，不属于运行时硬依赖。

