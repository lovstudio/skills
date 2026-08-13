# Skill Card — lov-icp-filing

## Description

在接入商与工信部链路中协助填写、提交和跟进 ICP 备案，明确实名同步、材料补充、短信核验、管局审核和服务备案号。

## Owner

LovStudio；由本地仓库维护者负责维护。

## License / Terms

MIT。可使用、修改和分发；实时监管结论以主管部门和接入商页面为准。

## Use Case

面向已有备案准备材料并需要办理或跟进 ICP 的网站负责人。核心任务：操作接入商备案订单；跟进实名、材料、短信核验和管局审核；仅在权威通过后记录服务备案号。

## Deployment Geography

中国大陆备案场景；作为 `lov-china-website-filing` 的自包含模块运行。

## Requirements / Dependencies

离线输出无外部依赖；实时操作使用用户自己的已登录会话。不得持久化验证码、Cookie 或完整证件数据。

## Known Risks and Mitigations

平台与地方规则可能变化，关键动作前重读权威页面；敏感资料最小化处理；完成状态必须满足本模块的真实证据门。

## References

- [Module instructions](SKILL.md)
- [Composition record](references/skill-composition.md)

## Skill Output

Markdown 权威状态快照和台账记录，包含订单、阶段、域名状态、用户动作、证据与时间。

## Skill Version

0.1.0

## Ethical Considerations

不伪造材料、不规避监管、不把推断写成权威结论；关键提交保留用户授权。

## LovStudio Evidence

### User Cases

见 [cases/cases.json](cases/cases.json)：lovstudio.cn 新增服务 ICP。

### Dimension Map

- 正确性：单一真实案例已验证。
- 安全性：提交门与隐私边界已审阅。
- 可追溯性：来源、时间、状态和下一动作已结构化。

当前不设置缺少多地区基线的数字评分。

### Pricing Basis

免费内嵌模块。避免错过短信核验、遗漏补充材料或把中间状态当成备案完成。 不包含代办保证、政府/云费用或法律意见。

### Distribution

`lovstudio` 为本地 Kit 内嵌；`github`、`workbuddy`、`skillpay` 均未发布。

