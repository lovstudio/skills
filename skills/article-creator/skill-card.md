# Skill Card — lov-article-creator

## Description

把事实材料变成一套完整微信公众号文章包：按题材组织正文和个人文风，生成官方品牌分享封面与 `4:3` 正文首图，并用机器质量门验收。研究评测类文章额外要求方法、Prompt、评分与复现链可追溯。

## Owner

LovStudio，联系入口：[lovstudio.ai](https://lovstudio.ai)。

## License / Terms

Skill 源码采用 MIT。输入文章、Logo、字体、图片和模型生成资产仍受各自来源、品牌与平台条款约束。

## Use Case

适合独立作者、研究团队、产品工作室和 Agent 开发者，从主题、资料或旧稿创建公众号长文；也可只审计已有文章包。它不负责未经授权的远端发布。

## Deployment Geography

面向全球的本地 Agent 环境，要求宿主能读取工作区文件并运行 Python。中文公众号是默认用例，但数据契约本身可迁移。

## Requirements / Dependencies

- Python 3.9+、PyYAML、Pillow 10+；
- 共享 Profile 中的发布主体名称与官方 raster Logo；
- 一张有合法使用权的艺术底图，或宿主图像生成能力；
- 本地创建不需要远端凭据。

## Known Risks and Mitigations

- 证据不足：先建立 truth ledger，不补造经历、引语和因果关系。
- 生图污染：艺术底图禁止文字与 Logo，品牌层后置合成并人工回读。
- 品牌或隐私泄露：只从 Profile 解析品牌，公开包扫描私有绝对路径。
- 状态夸大：生成后是 `pending_validation`，质量门通过后才是本地 `prepared`。

## References

- [Machine-readable card](skill-card.yaml)
- [Primary Skill instructions](SKILL.md)
- [Article template](references/article-template.md)
- [Cover system](references/cover-system.md)
- [Quality gate](references/quality-gate.md)

## Skill Output

每篇文章对应一个目录，包含 `article.md`、article/cover manifest、`sources.md`、无品牌艺术底图、`2.35:1` 分享封面 PNG/JPG、`4:3` 正文首图 PNG/JPG 和 `quality-report.json`。完整管线必须让校验器返回 `valid: true`。

## Skill Version

0.4.1

## Ethical Considerations

不伪造作者亲历、事实来源、官方 Logo 或发布状态；不把 Cookie、密钥、私人素材路径和内部工作备注写进公开制品。调用者负责确认外部材料与生成图片的使用权。

## LovStudio Evidence

### User Cases

首个真实案例来自《主流 Agent Harness 设计与实现 01：System Prompt》，见 [`cases/cases.json`](cases/cases.json)。成品已通过 23 项机器检查，其中包含手工川发布主体和白色横向 Logo lockup；本轮没有重新声称对文章事实做了全量复核。

### Dimension Map

维度统一为：事实与来源边界、编辑完整度、品牌一致性、机械可靠性、可移植与状态诚实。当前保留证据，不用主观数字冒充可比评分；详见 `skill-card.yaml`。

### Pricing Basis

0.2.0 免费开放本地验证。模型调用、素材授权、托管审批与代发布不属于免费 Skill 源码范围。

### Distribution

当前只有本地 canonical source 与共享安装入口可用。GitHub、LovStudio、WorkBuddy 和 SkillPay 均未发布或未准备，不描述为 live。
