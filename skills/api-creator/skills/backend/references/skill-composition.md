# Skill Group Composition

本模块是 `lov-api-creator` Skill Kit 的一部分，记录与相邻能力的边界。

## Nearby Skills Inspected

| Skill | Classification | Decision |
| --- | --- | --- |
| `lov-install-zenmux-api` | adjacent atom（不同网关槽位） | Supabase Edge Function 单一 AI 代理，与 uni-api 网关并列，无交接。 |
| `lov-refactor-api` | optional downstream atom | 创建网关端点后可选的冗余梳理；不是本模块的依赖。 |
| `lov-frontend`（同 Kit 模块） | downstream atom | 消费本模块产出的网关端点清单。 |

## Atomic Handoffs

```text
lov-backend
  网关端点清单（method + path + 说明）+ baseURL 约定
                |
                v
lov-frontend（同一 Kit 内的下游模块）
```

- 交接契约：网关端点清单（含请求/响应结构）与 baseURL 约定。
- 归属：本模块验收端点的正确性与可调用性。

## Overlap Decisions

与 `lov-install-zenmux-api` 的「网关」含义不同，槽位不重叠，保持独立。

## Composition Decision

本模块是 **Skill Kit 内嵌模块**：单一职责（uni-api 后端网关端点创建），与 `lov-frontend`
共同由控制器 `lov-api-creator` 通过 `full` 流水线编排；本身也可单独运行。
