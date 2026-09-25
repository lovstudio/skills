# Skill Group Composition

本模块是 `lov-api-creator` Skill Kit 的一部分，记录与相邻能力的边界。

## Nearby Skills Inspected

| Skill | Classification | Decision |
| --- | --- | --- |
| `lov-backend`（同 Kit 模块） | upstream atom | 产出网关端点清单，是本模块的输入契约来源。 |
| `lov-install-zenmux-api` | adjacent atom（不同槽位） | Supabase 代理是后端方案，前端调用层不消费其产物。 |
| `lov-refactor-api` | not composed | 后端重构，与前端封装无交接。 |

## Atomic Handoffs

```text
lov-backend（同一 Kit 内的上游模块）
  网关端点清单 + baseURL 约定
                |
                v
lov-frontend
  模块化 api/ 目录（request 封装 + 端点函数）
                |
                v
app 页面/组件 import 使用
```

- 交接契约：网关端点清单与 baseURL 约定；缺失时要求先执行 `lov-backend`。
- 归属：本模块验收前端封装的可用性。

## Overlap Decisions

前端调用层没有其它本地 Skill 承担同一职责；`lov-integrate-agent-uiux` 等 UI 集成能力不重叠。

## Composition Decision

本模块是 **Skill Kit 内嵌模块**：单一职责（uni-app 前端网关调用层封装），与 `lov-backend`
共同由控制器 `lov-api-creator` 通过 `full` 流水线编排；本身也可单独运行。
