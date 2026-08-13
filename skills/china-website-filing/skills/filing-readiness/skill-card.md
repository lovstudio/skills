# Skill Card — lov-filing-readiness

## Description

在提交中国大陆网站备案前，核验备案场景、主体与域名实名、接入资源、材料和专项义务风险，输出带来源等级的可执行准备清单。

## Owner

LovStudio；由本地仓库维护者负责维护。

## License / Terms

MIT。可使用、修改和分发；实时监管结论以主管部门和接入商页面为准。

## Use Case

面向准备在中国大陆服务器上线网站的企业、个人与技术负责人。核心任务：分类首次、新增服务、接入、变更或注销场景；核验主体、域名实名、接入资源和材料缺口；标记前置审批与安全评估风险。

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

Markdown 准备报告，包含场景、verified/user-stated/inferred/unknown 证据标签、阻塞项与下一步。

## Skill Version

0.1.0

## Ethical Considerations

不伪造材料、不规避监管、不把推断写成权威结论；关键提交保留用户授权。

## LovStudio Evidence

### User Cases

见 [cases/cases.json](cases/cases.json)：LovStudio 新增服务备案准备。

### Dimension Map

- 正确性：单一真实案例已验证。
- 安全性：提交门与隐私边界已审阅。
- 可追溯性：来源、时间、状态和下一动作已结构化。

当前不设置缺少多地区基线的数字评分。

### Pricing Basis

免费内嵌模块。减少因备案类型、实名不一致、材料或接入资源错误导致的反复退回。 不包含代办保证、政府/云费用或法律意见。

### Distribution

`lovstudio` 为本地 Kit 内嵌；`github`、`workbuddy`、`skillpay` 均未发布。

