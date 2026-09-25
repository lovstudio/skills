---
name: lov-frontend
description: >
  在 DCloud uni-app 前端项目里封装 API 网关调用层：统一 uni.request 封装（baseURL、token 注入、
  可复制的错误提示、SSE 流式支持），并按网关端点清单生成模块化 API 文件。触发：给 uni-app 封装
  网关请求层 / 前端对接网关 / wrap the gateway request layer in a uni-app project。
license: MIT
metadata:
  author: lovstudio
  version: "0.1.1"
  card_standard: lovstudio/skill-card/v1
  tags:
    - uni-app
    - gateway-client
  compatibility: "Portable Agent Skills format. 需要在 DCloud uni-app（含 pages.json 与 manifest.json）项目内执行。"
  dependencies: []
---

# 网关前端 · Gateway Frontend

在 DCloud uni-app 前端项目里生成一层网关调用封装：统一的 `request` 入口（baseURL / token / 错误
处理 / 流式），以及按后端网关端点清单生成的模块化 API 文件。页面与组件只 import 模块化 API，
不直接碰 `uni.request`。

## Triggers

### Activate when

- “给 uni-app 前端封装网关请求层”。
- “前端对接 uni-api 网关”。
- "wrap the gateway request layer in my uni-app project".
- "connect the uni-app frontend to the API gateway".

### Do not activate when

- 后端网关端点尚未在 uni-api 中建立：先跑本 Kit 的 `lov-backend` 模块。
- 目标是 H5/Web 或 Tauri 等非 uni-app 工程：封装位置不同，不适用本模块。

## User Profile (cross-session)

Every generated Skill is connected to the shared `user-profile/v1` contract in
`skill.yaml`. Read the shared user, brand, workspace, preferences, and this
Skill's `skills.<skill_id>` namespace at the start of every run. Keep the source
portable: resolved personal values belong in the shared profile, never here.

When the user directly states a durable preference or brand fact, persist it
through `scripts/profile_store.py` and report the saved profile path. Put
Skill-specific values under `records.<field>`; use `brand.<field>` or
`user.<field>` for shared values. Do not persist inferred secrets or credentials.
See `references/user-profile.md` for the complete contract.

## Skill Group Composition

Read `references/skill-composition.md` before deciding whether to invoke or
extend any adjacent capability. The record distinguishes optional upstream and
downstream handoffs from embedded Kit modules. Do not silently depend on a
sibling Skill that is not shipped with this source.

## Workflow (MANDATORY)

**You MUST follow these steps in order.**

### Step 0: Resolve skill root, dependencies, and runtime context

- Use `SKILL_DIR` if the environment provides it；否则从当前上下文推断已安装的模块目录。
- 确认工作目录是 DCloud uni-app 项目（根目录有 `pages.json` 与 `manifest.json`）。
- 确认网关 baseURL（后端部署地址）与鉴权方式（token 存于 `uni.getStorageSync` 的哪个 key）。
- 读取 `references/uni-app-client-patterns.md` 掌握 uni-app 请求约定。

Resolve `context.profile` on every invocation. The precedence is current request,
project context, Skill-specific profile records, shared preferences, shared
brand/user profile, then safe defaults. A direct user statement about a durable
preference or brand fact should be saved with `scripts/profile_store.py record`
using `--confirm`, followed by a concise saved-path report.

### Step 1: Understand the requested outcome

- 输入：后端**网关端点清单**（来自 backend 模块产物）、前端项目路径、baseURL、token 存取 key。
- 确认前端语言是 TS 还是 JS（决定生成 `.ts` 还是 `.js`）。
- 最终交付：可 import 的 `api/` 模块 + 一个页面调用示例 + 用法说明。

### Step 1.5: Analyze nearby Skills before implementation

- 确认无需依赖后端网关之外的其它能力；若端点清单缺失，回退要求先执行 `lov-backend`。

### Step 2: Execute the workflow

1. **baseURL 配置**：在 `api/config.ts`（或等价位置）集中放 baseURL；dev/prod 可按 `process.env`
   或 `uni.getSystemInfoSync().platform` 等区分，不散落在页面里。
2. **request 封装**：新建 `api/request.ts`，对 `uni.request` 做 Promise 化：
   - 自动拼接 baseURL 与 path；超时、`Content-Type` 按需设置。
   - **token 注入**：`Authorization: Bearer <token>`，token 从 `uni.getStorageSync(key)` 读取，
     支持自定义 getter。
   - **错误处理**：非 2xx 或网关错误结构（如 `standard_error_handler` 的 `detail`）统一抛错，
     提示信息可复制并携带 `context_id`/`requestId` 等便于 debug 的字段。
   - **401 处理**：回调刷新 token 或跳登录页，避免页面各自处理。
   - **流式（按需）**：SSE 端点用 `uni.request` 的 `enableChunked` 或事件源适配器封装。
3. **端点模块**：按后端端点清单生成 `api/<domain>.ts`，每个端点一个函数（如 `api/llm.ts` 的
   `callBase(body)`），页面直接 `import { callBase } from '@/api/llm'`。
4. **类型**：`api/types.ts` 定义网关响应与错误类型；TS 工程用 `interface`，JS 工程可省。
5. **示例**：在一个页面（或文档注释）给出最小调用示例，并验证一次真实调用。

### Step 3: Validate the deliverable

- request 封装可被页面 import 后正常调用；错误提示可复制且含上下文。
- 每个端点模块导出函数与端点清单一一对应。
- 汇报：baseURL 配置位置、request 用法示例、各模块导出函数清单。

## Dependencies

- DCloud uni-app 项目；仅使用 `uni.request` 等内置 API，无第三方依赖。
- 需要后端网关端点清单作为输入。
