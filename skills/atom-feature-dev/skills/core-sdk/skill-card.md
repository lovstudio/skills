# 功能共享内核 · Feature Core · Skill Card

## Description

基于已批准契约实现唯一业务核心与类型化 SDK，为所有分发 adapter 提供同一调用边界。

## Owner

LovStudio Skill source maintainers。

## License / Terms

MIT；目标项目和第三方依赖遵循各自许可证。

## Use Case

实现共享 SDK 并验证真实包入口。本模块只在根 Atom Feature Kit 内承担这一阶段，不接管其他模块结果。

## Deployment Geography

全球；在本地目标仓库和其已授权运行环境中使用。

## Requirements / Dependencies

需要根 atom feature manifest、相邻内嵌模块的明确制品交接和目标项目自己的工具链。

## Known Risks and Mitigations

adapter 中残留业务规则会导致跨形态漂移。 把默认值、校验和状态迁移集中到 SDK，并用共享向量验证。

## References

- [Module instructions](SKILL.md)
- [Composition record](references/skill-composition.md)

## Skill Output

SDK 制品、公开类型、错误映射与测试证据。只有真实制品与验证证据齐全时才标记 verified。

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

