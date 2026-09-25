# 网关工坊 · Gateway Studio · Skill Card

This human-readable card mirrors `skill-card.yaml`. It is a release record, not
an implementation note. A reviewer should understand the Skill without opening
its source.

## Description

当开发某个 app 需要 API 网关能力时，本 Skill 在 uni-api（FastAPI 聚合网关）后端为该 app 创建
网关端点并接入 /docs 分组，同时在对应 uni-app 前端封装统一调用层，让 app 通过网关访问聚合 API。
以 Skill Kit 形式提供：backend 模块产出网关端点清单，frontend 模块消费该清单封装前端调用层。

## Owner

手工川工作室（Lovstudio.AI），联系人 shawninjuly@gmail.com。

## License / Terms

MIT。源码可自由使用、修改与分发；保留版权声明。

## Use Case

面向使用 uni-api 作为聚合网关并开发 DCloud uni-app 前端的开发者。当开发某个 app 需要网关能力
（聚合上游 API、统一鉴权与错误处理）时，一键集成到 uni-api 后端并在 uni-app 前端封装调用层。

## Deployment Geography

在 uni-api FastAPI 后端仓库与 DCloud uni-app 前端仓库内生成代码；无远程部署动作。

## Requirements / Dependencies

- 可访问的 uni-api（FastAPI）仓库，遵循仓库 AGENTS.md 的运行前提（.env 必填字段、socksio 等）。
- DCloud uni-app 项目（含 pages.json 与 manifest.json）。
- 无第三方外部服务依赖。

## Known Risks and Mitigations

- 改动破坏 uni-api 启动（.env 缺字段、OSSClient 启动失败等）→ 先读 AGENTS.md 满足前提，
  验收用 python import main 确认不破坏启动。
- 后端端点与前端封装契约不一致 → 以 backend 产出的端点清单作为 frontend 输入，逐条核对导出函数。
- 前端错误提示不含上下文难排查 → 统一错误结构携带 context_id 与请求信息，报错 UI 支持复制。

## References

- [Machine-readable card](skill-card.yaml)
- [Primary Skill instructions](SKILL.md)
- [Backend module](skills/backend/SKILL.md)
- [Frontend module](skills/frontend/SKILL.md)

## Skill Output

- 后端网关端点（FastAPI router + config/app_groups 分组配置）。
- 前端 api/ 调用层（request 封装 + 端点模块）。
- 网关端点清单与用法示例。

## Skill Version

0.1.0

## Ethical Considerations

本 Skill 生成网关代码不涉及内容生成；避免在源码中硬编码密钥，上游密钥只存环境变量与 .env。
不采集用户隐私，不绕过任何平台访问限制。

## LovStudio Evidence

### User Cases

See [`cases/cases.json`](cases/cases.json). 首条案例记录了驱动本 Skill 创建的真实需求
（在 uni-api 内集成 app 网关能力并封装 uni-app 调用层）；端到端执行案例待首个真实 app 跑通后回填。

### Dimension Map

- correctness：端点与约定正确性，evidence 为遵循仓库既有模式且验收 import 通过。
- effectiveness：契约一致性，evidence 为端点清单与前端导出函数逐条对应。
- efficiency：封装复用效率，evidence 为错误/token/baseURL 集中在 request 与 config。

### Pricing Basis

免费。内部开发提效 skill，随手工川工作室公开分发。

### Distribution

免费渠道：github、lovstudio。付费渠道（workbuddy、skillpay）当前不启用。
