# 网关后端 · Gateway Backend · Skill Card

This human-readable card mirrors `skill-card.yaml`. It is a release record, not
an implementation note.

## Description

在 uni-api（FastAPI 聚合网关）项目内为某个 app 新增网关能力：新建业务 package 与 router，
注册进 router/__init__.py，并把 tag 分组加入 config/app_groups.py，让该 app 通过 uni-api
网关调用聚合后的上游 API。

## Owner

手工川工作室（Lovstudio.AI），联系人 shawninjuly@gmail.com。

## License / Terms

MIT。源码可自由使用、修改与分发；保留版权声明。

## Use Case

后端开发者需要为某个 app 暴露一组后端网关端点并接入 /docs 分组时使用。

## Deployment Geography

在 uni-api FastAPI 后端仓库内生成代码；无远程部署动作。

## Requirements / Dependencies

- uni-api 仓库，遵循 AGENTS.md 运行前提（.env 必填字段、socksio 等）。
- python3 与项目 poetry 环境。

## Known Risks and Mitigations

- 改动破坏 uni-api 启动 → 先读 AGENTS.md，验收用 python import main 确认。
- 端点在 /docs 分组缺失 → 把 tag 加入 config/app_groups.py 并核对 openapi。

## References

- [Machine-readable card](skill-card.yaml)
- [Backend module instructions](SKILL.md)
- [uni-api patterns](references/uni-api-patterns.md)

## Skill Output

- FastAPI router 与 config/app_groups.py 分组配置。
- 网关端点清单（method + path + 说明），作为下游 frontend 模块的输入契约。

## Skill Version

0.1.0

## Ethical Considerations

不硬编码密钥，上游密钥只存环境变量与 .env；不绕过任何平台访问限制。

## LovStudio Evidence

### User Cases

See [`cases/cases.json`](cases/cases.json)。首条案例记录驱动 Skill Kit 创建的真实需求。

### Dimension Map

- correctness：约定正确性，evidence 为与仓库既有模式对齐且 import 通过。
- effectiveness：端点可调用，evidence 为错误结构统一且端点清单交付下游。
- maintainability：可维护性，evidence 为业务逻辑与路由分层。

### Pricing Basis

免费，随 lov-api-creator Kit 分发。

### Distribution

免费渠道：github、lovstudio。付费渠道当前不启用。
