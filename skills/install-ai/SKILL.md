---
name: lov-install-ai
description: >
  为现有或新 App 快速初始化可上线的 AI 功能，可选择本地 Agent Client、MaaS 中转渠道、模型偏好和配套 UI。用户说集成 AI、给 App 加聊天/生成能力、Agent Client、MaaS 或模型选择时使用。
license: MIT
metadata:
  author: lovstudio
  version: "0.1.1"
  tags:
    - ai
    - maas
    - agent-client
    - app-integration
  compatibility: "Web, mobile, and desktop apps; production network calls require a server-side or desktop-local adapter."
  dependencies: []
---

# 安装 AI 功能

把一个 App 的 AI 能力从产品入口、调用通道、模型策略到可选 UI 一次接好；生成的用户界面只呈现用户需要的能力，不暴露本次需求中的背景、账户或渠道细节。

## Triggers

### Activate when

- 用户说“给这个 App 加 AI 功能”“初始化 AI 调用”或“加一个聊天/总结/生成入口”。
- 用户提到 Agent Client、MaaS 中转渠道、模型偏好、模型路由或可选 AI UI。
- User asks to “add AI to this app”, “bootstrap an AI feature”, or “connect an app to an Agent Client or MaaS”.

### Do not activate when

- 用户只要在开发环境调用一个已有脚本或一次性模型测试；使用当前项目的开发工具链。
- 用户只要配置某个 Agent Client 的全局账号或 API Key，而不改 App 功能；使用该 Client 或 MaaS 的配置流程。

## User Configuration

This Skill stores only portable preferences such as route order, model intent, language, and UI default. Resolve them through [references/user-config.md](references/user-config.md); never store API keys, tokens, private endpoints, or project paths in source control.

## Workflow (MANDATORY)

**You MUST follow these steps in order.**

### Step 0: Inspect the App and define one user outcome

- Identify the stack, runtime surfaces, authentication model, existing backend boundary, and the user action that AI improves.
- Separate internal implementation context from product copy. Do not put provider names, personal notes, model names, or setup history in the user-facing UI unless they are a deliberate user choice.
- Default to one narrow capability such as rewrite, extract, classify, chat with a scoped source, or generate a structured draft; do not add a generic chat box without a product job.

### Step 1: Resolve the integration choices

- Reuse explicit project context and saved preferences first. If a choice remains product-visible, present this compact selection:
  1. **Agent Client** — use only when the App runs locally and the user has a compatible local Client/bridge.
  2. **MaaS** — use a server-side gateway for web, mobile, shared, or production traffic.
  3. **Hybrid** — use MaaS as the product runtime and an Agent Client only for local desktop/developer enhancement.
- Select a model intent rather than hard-coding a provider model: `fast`, `balanced`, `reasoning`, `vision`, or `creative`.
- Ask whether user-facing UI is needed only when the feature can reasonably be headless or interactive. Infer a focused UI for user-initiated App features.
- Read [references/runtime-routing.md](references/runtime-routing.md) and, when adding UI, [references/ai-feature-ui.md](references/ai-feature-ui.md).

### Step 2: Add the product boundary

- Create one typed feature contract: input, validated request, selected model intent, streamed or non-streamed response, error shape, and usage metadata.
- Put MaaS credentials and upstream routing on a server-side gateway. The browser/mobile client calls the App's own endpoint, never an upstream secret directly.
- Implement Agent Client support behind the same adapter contract. Detect availability at runtime; expose a clear unavailable state and do not block the whole App when it is absent.
- Keep provider routing, retries, rate limits, telemetry, and raw provider errors outside user-visible copy.

### Step 3: Add UI only when the product needs it

- Reuse the App's existing component, locale, loading, and error conventions.
- Build the smallest complete interaction: purposeful entry point, input constraints, pending state, result rendering, retry, and accessible keyboard behavior.
- Show model preference only when the end user benefits from controlling trade-offs. Otherwise keep it as a product or profile preference.
- For generated content, provide a next action meaningful to the App: insert, apply, save, copy, compare, or discard.

### Step 4: Validate an end-to-end route

- Test Agent Client present, Agent Client absent, MaaS success, MaaS failure, slow or streaming response, and malformed model output as applicable.
- Verify no credential, internal route, provider stack trace, or private prompt appears in source, network payloads, logs, or final UI.
- Run the target project's format, lint, typecheck, tests, and a real user interaction through the selected route.
- Report the chosen runtime route, configured model intent, UI decision, fallback behavior, and user-visible result.

## Dependencies

- A target App with a known frontend and/or server boundary.
- A compatible local Agent Client bridge, a configured MaaS gateway, or both.
