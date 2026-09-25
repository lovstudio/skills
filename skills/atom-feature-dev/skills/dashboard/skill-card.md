# 功能控制台 · Feature Dashboard · Skill Card

## Description

提供可运行 Atom Workbench，读取真实 manifest、Profile、surface 运行结果与运营证据，完成
切换、执行、对比和 Review。

## Owner

LovStudio Skill source maintainers。

## License / Terms

MIT；目标项目和第三方依赖遵循各自许可证。

## Use Case

实现 atom index、Run、Compare 与 Evidence。本模块只在根 Atom Feature Kit 内承担这一阶段，不接管其他模块结果。

## Deployment Geography

全球；在本地目标仓库和其已授权运行环境中使用。

## Requirements / Dependencies

需要 Python 3.8+、根 atom feature manifest、相邻内嵌模块的明确制品交接和目标项目工具链。

## Known Risks and Mitigations

手填状态会让面板把实现或构建误报为验证和发布。 状态只来自 manifest、测试报告和运行回读，verified 与 released 需要证据。

## References

- [Module instructions](SKILL.md)
- [Composition record](references/skill-composition.md)
- [Companion Dashboard](../../dashboard/README.md)

## Skill Output

可运行 Dashboard route、loopback bridge、data adapter、组件与真实交互证据。只有真实目标
项目制品与验证证据齐全时才标记 verified。

## Skill Version

0.2.1

## Ethical Considerations

保护秘密与用户 Profile，不虚构案例、分数、运行、用户或发布状态。

## LovStudio Evidence

### User Cases

当前案例包含内置 Dashboard HTTP、workspace 回读、manifest-declared SDK command selftest，
headless Chrome 桌面运行、390px 响应式验收，以及无资源错误的 file URL 只读预览；尚未
声称任何外部目标项目完成 UI 运行验收。

### Dimension Map

卡片记录边界、正确性与证据三类维度，真实项目分数保持未赋值。

### Pricing Basis

作为根 Kit 的内嵌模块免费提供；托管、外部服务和定制工程不在边界内。

### Distribution

本模块只随根 Kit 本地安装，所有外部渠道均未发布。
