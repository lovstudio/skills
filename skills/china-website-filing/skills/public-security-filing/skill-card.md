# Skill Card — lov-public-security-filing

## Description

为已取得 ICP 并开放的网站准备和提交公安联网备案，核验主体、网站与接入信息，跟进属地审核并独立处理安全评估分支。

## Owner

LovStudio；由本地仓库维护者负责维护。

## License / Terms

MIT。可使用、修改和分发；实时监管结论以主管部门和接入商页面为准。

## Use Case

面向已上线中国大陆网站且需履行公安联网备案义务的单位或个人。核心任务：填写主体、网站、域名与服务器信息；在人工确认后提交并跟进属地审核；取得公安号后上线平台代码并分流安全评估。

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

Markdown 申请/审核状态、补充动作、审核单位、公安备案号与页脚验收；安全评估另列状态。

## Skill Version

0.1.0

## Ethical Considerations

不伪造材料、不规避监管、不把推断写成权威结论；关键提交保留用户授权。

## LovStudio Evidence

### User Cases

见 [cases/cases.json](cases/cases.json)：飞脑科技公安联网备案提交。

### Dimension Map

- 正确性：单一真实案例已验证。
- 安全性：提交门与隐私边界已审阅。
- 可追溯性：来源、时间、状态和下一动作已结构化。

当前不设置缺少多地区基线的数字评分。

### Pricing Basis

免费内嵌模块。减少字段错配、主体账号混淆、超期和误启动额外安全评估的风险。 不包含代办保证、政府/云费用或法律意见。

### Distribution

`lovstudio` 为本地 Kit 内嵌；`github`、`workbuddy`、`skillpay` 均未发布。

