# Skill Group Composition

本记录随每次生成/调用更新，防止相邻 Skill 变成意外重复或隐藏依赖。

## Nearby Skills Inspected

| Skill | Classification | Decision |
| --- | --- | --- |
| `lov-install-zenmux-api` | adjacent atom（不同网关槽位） | 在 Supabase Edge Function 里做单个 AI 供应商代理（如 Gemini 生图）；与 uni-api 网关是并列方案，不构成交接，保持独立。 |
| `lov-refactor-api` | optional downstream atom | 创建网关端点后如需梳理冗余 API 可选调用；不依赖本 Skill 存在。 |
| `lov-app-generator` / `lov-oh-my-landingpage` | not composed | 生成独立 App 工程或落地页，与本 Skill 的网关集成无交接。 |
| `lov-deploy-to-vercel` | not composed | 网关部署上线是独立能力；本 Skill 在仓库内生成代码，不负责部署。 |
| `lov-backend`（本 Kit 模块） | core atom | 在 uni-api 后端创建网关端点，产出端点清单。 |
| `lov-frontend`（本 Kit 模块） | core atom | 消费端点清单，在 uni-app 前端封装调用层。 |

## Atomic Handoffs

```text
lov-backend
  网关端点清单（method + path + 说明）+ baseURL 约定
                |
                v
lov-frontend
  模块化 api/ 目录（request 封装 + 端点函数）
                |
                v
app 页面/组件 import 使用
```

- 交接契约：**网关端点清单**（由 backend 模块产出，含 baseURL 约定）是 frontend 模块的输入。
- 归属：backend 模块拥有端点的正确性与可调用性验收；frontend 模块拥有前端封装的可用性验收。
- 无其它外部交接：`lov-refactor-api`、`lov-install-zenmux-api` 均为可选，不是隐藏依赖。

## Overlap Decisions

- `lov-install-zenmux-api` 与 uni-api 网关都叫「网关」，但槽位不同：一个是 Supabase Edge
  Function 的单一 AI 代理，一个是 FastAPI 聚合网关。保留各自独立，不互相调用。
- `lov-refactor-api` 在「后端 API」领域相邻，但职责是事后重构冗余；不并入本 Kit。

## Composition Decision

本 Skill 是**自包含 Skill Kit**：backend（网关端点创建）与 frontend（调用层封装）两个阶段
各有独立输入/输出契约且可单独使用（`backend` / `frontend` 单流水线），又能以 `full` 流水线
（backend → frontend）一次完成用户可见的同一结果。两个模块均内嵌在本仓库，无外部 sibling 依赖。
