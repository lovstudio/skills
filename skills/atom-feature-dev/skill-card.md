# 功能工坊 · Feature Studio · Skill Card

## Description

把一个原子功能实现为共享 SDK、多种分发 adapter、Profile Preset、运营配套与可运行的
Atom Workbench，并用同一测试向量验证跨形态一致性。

## Owner

LovStudio Skill source maintainers。

## License / Terms

MIT。目标项目和第三方依赖继续遵循各自许可证。

## Use Case

适用于一个业务能力需要同时面向程序、命令行、互联网服务、普通用户和 Agent 分发的场景。
输入为目标仓库与一个可独立验收的用户结果；输出为完整实现和证据，不是松散架构建议。

## Deployment Geography

全球；默认在本地目标仓库运行，外部部署与发布需要单独授权。

## Requirements / Dependencies

Python 3.8+ 运行 manifest helper，目标仓库自己的语言、构建和测试工具，以及只作用于受众
可见文案的 `lov-branding-consistency`。

## Known Risks and Mitigations

主要风险是 adapter 漂移、Profile 隐藏错误默认值、Dashboard 夸大状态。Skill 通过单一 SDK、
共享测试向量、参数来源显示和 evidence gate 控制这些风险。

## References

- [Primary Skill instructions](SKILL.md)
- [Atom Feature Contract](references/atom-feature-contract.md)
- [Acceptance Matrix](references/acceptance-matrix.md)
- [Companion Dashboard](dashboard/README.md)

## Skill Output

输出 JSON manifest、共享 SDK 和 adapters、Profile Preset 体验、Operations 矩阵、可运行的
Atom Workbench 与测试/运行证据。目标 atom 至少需要一个测试向量跨两个适用 surface 通过。

## Skill Version

0.2.1

## Ethical Considerations

不持久化秘密，不在日志和 Dashboard 暴露个人 Profile，不虚构用户、指标或上线状态，未经
明确授权不发布、上传或修改共享权限。

## LovStudio Evidence

### User Cases

当前真实案例包括本 Skill Kit 的创建请求，以及后续 ADE 式 Companion Dashboard 的实现请求，
见 [`cases/cases.json`](cases/cases.json)。它们证明需求、模块契约、本地 HTTP 回读、file URL
只读预览与示例 surface 执行；尚未声称完成任一外部目标项目 atom。

### Dimension Map

维度包括契约完整性、跨形态一致性、自动化体验和运营状态真实性。当前只记录可回读证据，
真实项目分数保持未赋值。

### Pricing Basis

当前免费，用于验证多形态原子功能方法。边界与复评条件见
[`pricing-card.yaml`](pricing-card.yaml)。

### Distribution

当前仅完成本地真源与安装。GitHub、LovStudio、WorkBuddy 和 SkillPay 均未发布。
