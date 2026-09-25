# 网关前端 · Gateway Frontend · Skill Card

This human-readable card mirrors `skill-card.yaml`. It is a release record, not
an implementation note.

## Description

在 DCloud uni-app 前端项目里封装 API 网关调用层：统一 uni.request 封装（baseURL、token 注入、
可复制的错误提示、SSE 流式支持），并按网关端点清单生成模块化 API 文件，页面只 import 端点函数。

## Owner

手工川工作室（Lovstudio.AI），联系人 shawninjuly@gmail.com。

## License / Terms

MIT。源码可自由使用、修改与分发；保留版权声明。

## Use Case

前端开发者需要把后端网关的调用收敛到统一封装，页面不直接碰 uni.request 时使用。

## Deployment Geography

在 DCloud uni-app 前端项目内生成代码；无远程部署动作。

## Requirements / Dependencies

- DCloud uni-app 项目（含 pages.json 与 manifest.json）。
- 后端网关端点清单（来自 lov-backend 模块）。
- 仅使用 uni.request 等内置 API，无第三方依赖。

## Known Risks and Mitigations

- 错误提示不含上下文难排查 → 统一错误结构携带 context_id 与请求信息，报错 UI 支持复制。
- 导出函数与后端端点不一致 → 按清单逐条生成并核对。

## References

- [Machine-readable card](skill-card.yaml)
- [Frontend module instructions](SKILL.md)
- [uni-app client patterns](references/uni-app-client-patterns.md)

## Skill Output

- api/ 目录：request 封装 + config + types + 端点模块。
- 用法示例与调用验证结果。

## Skill Version

0.1.0

## Ethical Considerations

不采集用户隐私；token 仅存本地 storage，不落日志；不绕过任何平台访问限制。

## LovStudio Evidence

### User Cases

See [`cases/cases.json`](cases/cases.json)。首条案例记录驱动 Skill Kit 创建的真实需求。

### Dimension Map

- correctness：封装正确性，evidence 为页面完成一次真实调用。
- effectiveness：契约一致性，evidence 为导出函数与端点清单一一对应。
- efficiency：复用效率，evidence 为错误/token/baseURL 集中封装。

### Pricing Basis

免费，随 lov-api-creator Kit 分发。

### Distribution

免费渠道：github、lovstudio。付费渠道当前不启用。
