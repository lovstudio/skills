# Skill Card — lov-china-website-filing

## Description

按权威页面协助完成中国大陆网站的备案准备、ICP、备案后域名切换、公安联网备案与持续巡检，并保留人工提交门和追加式证据台账。

## Owner

LovStudio；由本地仓库维护者负责维护。

## License / Terms

MIT。可使用、修改和分发；监管结论始终以主管部门和接入商实时页面为准。

## Use Case

适合在中国大陆服务器上线网站的负责人、开发者和小团队。输入主体、服务、域名、接入资源与已有订单，输出分阶段准备清单、操作证据、状态台账和完成验收。

## Deployment Geography

中国大陆备案场景；Skill 本身可在任意支持 Python 3.8+ 和 Portable Agent Skills 的本地环境运行。

## Requirements / Dependencies

离线台账只需 Python 标准库。源校验需要 PyYAML；真实办理需要网络、浏览器控制能力和用户自己的已登录会话。

## Known Risks and Mitigations

- 法规和地方口径变化：关键动作前重读官方或接入商页面并记录日期。
- 误报完成：ICP、上线、公安备案、安全评估分别验收。
- 非真实申报：业务分类、责任书、验证码、最终提交保留人工确认。
- 隐私泄漏：不在源码、Profile、日志或案例保存完整证件号、验证码、Cookie 和扫描件内容。

## References

- [Machine-readable card](skill-card.yaml)
- [Primary Skill instructions](SKILL.md)
- [Official rules snapshot](references/official-rules.md)
- [Authority gates](references/authority-gates.md)
- [Status taxonomy](references/status-taxonomy.md)

## Skill Output

Markdown 准备/状态/验收报告与追加式 Markdown 台账；CLI 同时输出 JSON 差异结果。完整性检查要求权威入口、核验时间、阶段状态、用户动作与证据摘要齐全。

## Skill Version

0.1.0

## Ethical Considerations

不规避监管、不伪造材料、不代替法律意见，也不在缺少授权时接受责任书、处理验证码或提交高影响申请。

## LovStudio Evidence

### User Cases

[`cases/cases.json`](cases/cases.json) 记录了 `lovstudio.cn` 从 ICP 新增服务通过、域名上线到公安联网备案待审核的真实 Input → Prompt → Output。

### Dimension Map

| 维度 | 当前状态 | 证据 |
| --- | --- | --- |
| 权威正确性 | 单一真实案例已验证 | ICP、上线、公安状态分别取证 |
| 提交与隐私安全 | 单一真实案例已验证 | 最终提交经确认，案例已去除私密字段 |
| 可追溯性 | 本地测试通过 | 台账 CLI 的 init/append/compare/check |
| 可移植性 | 本地源校验 | 无个人绝对路径、无单一厂商硬依赖 |

当前不以未经定义的数字分数代替证据；扩大到多地区、多接入商案例后再建立量化基线。

### Pricing Basis

当前为免费本地 Skill。它包含流程、台账脚本和案例，不包含代办保证、云资源、政府费用或法律意见；法规/平台重大变化或新增人工 SLA 时复评。

### Distribution

- `lovstudio`: 已本地安装，未发布远程目录。
- `github`: 未发布。
- `workbuddy`: 未发布。
- `skillpay`: 未发布。
