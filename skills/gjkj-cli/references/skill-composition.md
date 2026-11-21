# Skill Group Composition

## Nearby Skills Inspected

| Skill | Routing contract | Relation |
| --- | --- | --- |
| `lov-cli2anything` | 把授权的 API 证据生成 OpenAPI、SDK、Swagger、CLI；已有 suanli.cn 适配器 | **upstream atom**：生成 `assets/cli/`；接口变化时由它重新生成 |
| `lov-cli-creator` | 为本地应用或源码项目从零设计 CLI | not composed：本 Skill 不设计新 CLI |
| `lov-api-creator` | 为 uni-app 增加 FastAPI 聚合网关 | not composed |
| `ego-browser` | 浏览器操作 | tool：打开本地 Swagger；控制台操作（建密钥、充值）由用户本人完成 |

## Atomic Handoffs

1. `lov-cli2anything` → 本 Skill：生成目录（`openapi.json`、`sdk/`、`bin/`、`swagger/`、`manifest.json`、`api-graph.json`）整体放进
   `assets/cli/`；验收是 `doctor` 通过与一次只读调用成功（references/regenerate.md）。
2. 本 Skill → 用户：查询结果摘要、写操作前的 dry-run 请求、写操作后的回查结果。

## Overlap Decisions

- 不把调用规则写进 `lov-cli2anything`：那个 Skill 负责「生成」，本 Skill 负责「在对话里安全地用」。生成器保持通用，平台专属的
  确认规则、密钥约定与错误解释放在这里。

## Composition Decision

Single Skill：一个用户结果（调用共绩算力 API），随附生成好的 CLI 与 SDK，运行时不依赖其他 Skill。
