# 功能参数配置 · Feature Presets · Skill Card

## Description

从共享参数 schema 构建前端 Preset 编辑与解析体验，让 Agent 优先使用用户配置并减少追问。

## Owner

LovStudio Skill source maintainers。

## License / Terms

MIT；目标项目和第三方依赖遵循各自许可证。

## Use Case

实现 Profile Preset、参数来源与显式覆盖。本模块只在根 Atom Feature Kit 内承担这一阶段，不接管其他模块结果。

## Deployment Geography

全球；在本地目标仓库和其已授权运行环境中使用。

## Requirements / Dependencies

需要根 atom feature manifest、相邻内嵌模块的明确制品交接和目标项目自己的工具链。

## Known Risks and Mitigations

过期或隐私参数可能被静默复用。 展示来源、校验版本、支持覆盖，并禁止持久化秘密和一次性输入。

## References

- [Module instructions](SKILL.md)
- [Composition record](references/skill-composition.md)

## Skill Output

Preset 编辑器、resolver、微文案和交互证据。只有真实制品与验证证据齐全时才标记 verified。

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

