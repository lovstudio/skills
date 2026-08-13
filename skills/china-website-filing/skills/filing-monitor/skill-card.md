# Skill Card — lov-filing-monitor

## Description

按计划打开备案权威页面，比较上一条状态并追加台账；无变化时静默，状态变化、登录阻塞、补充材料或完成门满足时再通知。

## Owner

LovStudio；由本地仓库维护者负责维护。

## License / Terms

MIT。可使用、修改和分发；实时监管结论以主管部门和接入商页面为准。

## Use Case

面向需要持续跟进 ICP、公安备案或安全评估的个人、企业和运维负责人。核心任务：读取权威订单或申请详情；比较并追加状态台账；按用户策略通知、保留 handoff 页面或暂停巡检。

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

Markdown 追加式巡检记录与 JSON 差异结果，包含 changed 和 needs_user_action。

## Skill Version

0.1.0

## Ethical Considerations

不伪造材料、不规避监管、不把推断写成权威结论；关键提交保留用户授权。

## LovStudio Evidence

### User Cases

见 [cases/cases.json](cases/cases.json)：lovstudio.cn ICP 每日静默巡检。

### Dimension Map

- 正确性：单一真实案例已验证。
- 安全性：提交门与隐私边界已审阅。
- 可追溯性：来源、时间、状态和下一动作已结构化。

当前不设置缺少多地区基线的数字评分。

### Pricing Basis

免费内嵌模块。减少重复人工查看和无效提醒，同时保留可审计的状态变化与人工接管点。 不包含代办保证、政府/云费用或法律意见。

### Distribution

`lovstudio` 为本地 Kit 内嵌；`github`、`workbuddy`、`skillpay` 均未发布。

