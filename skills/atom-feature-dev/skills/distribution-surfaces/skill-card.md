# 功能多端分发 · Feature Distribution · Skill Card

## Description

从同一 Core SDK 实现适用的 CLI、REST API 与 Agent Skill adapter，并验证规范化结果等价。

## Owner

LovStudio Skill source maintainers。

## License / Terms

MIT；目标项目和第三方依赖遵循各自许可证。

## Use Case

建立多形态 adapter 与跨 surface 测试。本模块只在根 Atom Feature Kit 内承担这一阶段，不接管其他模块结果。

## Deployment Geography

全球；在本地目标仓库和其已授权运行环境中使用。

## Requirements / Dependencies

需要根 atom feature manifest、相邻内嵌模块的明确制品交接和目标项目自己的工具链。

## Known Risks and Mitigations

传输包装差异可能被误判为业务差异。 比较规范化业务结果、错误类别和副作用，显式声明允许差异。

## References

- [Module instructions](SKILL.md)
- [Composition record](references/skill-composition.md)

## Skill Output

CLI、API、Agent 入口、schema 与验证证据。只有真实制品与验证证据齐全时才标记 verified。

## Skill Version

0.1.0

## Ethical Considerations

保护秘密与用户 Profile，不虚构案例、分数、运行、用户或发布状态。

## LovStudio Evidence

### User Cases

当前案例记录本 Kit 创建过程中已落盘的模块契约；尚未声称在目标项目完成运行实现。

### Dimension Map

卡片记录边界、正确性与证据三类维度，真实项目分数保持未赋值。

### Pricing Basis

作为根 Kit 的内嵌模块免费提供；托管、外部服务和定制工程不在边界内。

### Distribution

本模块只随根 Kit 本地安装，所有外部渠道均未发布。

