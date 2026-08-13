# Skill Card — lov-domain-cutover

## Description

在 ICP 通过后安全配置部署、DNS、证书和备案页脚，用真实域名回读验证 HTTPS 与站点内容，并按授权处理旧域名。

## Owner

LovStudio；由本地仓库维护者负责维护。

## License / Terms

MIT。可使用、修改和分发；实时监管结论以主管部门和接入商页面为准。

## Use Case

面向已取得 ICP 服务备案号并准备开放中国大陆网站的站点负责人。核心任务：绑定备案域名并配置 DNS/TLS；添加并核验 ICP 服务备案号；按明确授权处理旧域名并保留回读证据。

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

Markdown 上线验收报告，包含 DNS、证书、HTTP 页面、备案页脚和旧域名结果。

## Skill Version

0.1.0

## Ethical Considerations

不伪造材料、不规避监管、不把推断写成权威结论；关键提交保留用户授权。

## LovStudio Evidence

### User Cases

见 [cases/cases.json](cases/cases.json)：lovstudio.cn 备案后切换上线。

### Dimension Map

- 正确性：单一真实案例已验证。
- 安全性：提交门与隐私边界已审阅。
- 可追溯性：来源、时间、状态和下一动作已结构化。

当前不设置缺少多地区基线的数字评分。

### Pricing Basis

免费内嵌模块。防止未备案提前开放、证书主机名错误、DNS 误切和备案号只在代码中存在却未上线。 不包含代办保证、政府/云费用或法律意见。

### Distribution

`lovstudio` 为本地 Kit 内嵌；`github`、`workbuddy`、`skillpay` 均未发布。

