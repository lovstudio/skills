# Skill Card — lov-skill-add-case

## Description

把一次已明确认可的 Skill 结果整理成官网案例，支持网页 JSON 导入或 Agent
登录投稿，保留最终成品、真实证据和发布前确认。

## Owner

LovStudio Skill contributors；维护入口为源仓库。

## License

MIT，详见 [`LICENSE`](LICENSE)。

## Use Case

适合在一次 Skill 调用完成并由用户明确确认满意后，补充该 Skill 的公开证据。

## Deployment Geography

离线生成 JSON；在线投稿使用 LovStudio 官网账号与服务。

## Requirements / Dependencies

需要 Python 3.10+。直接投稿复用 `lov-share-session` 登录，普通 LovStudio 账号
即可，无需 GitHub 权限；PyYAML 仅用于源码校验。完整会话不是必填项。

## Known Risks and Mitigations

- 未获用户认可：硬性验收门阻止写入。
- 泄露私有信息：高风险模式检查、隐私说明和完整预览确认。
- 同意后内容变动：发布要求用户审阅过的完整内容指纹。
- 付费 Session 混入普通投稿：官网仅接受可选的本人公开链接，付费维护者路径单独授权。
- 把提交当上线：公开 JSON 指纹、实际页面、图片及可选 Session 回读。

## References

- [Machine-readable card](skill-card.yaml)
- [Primary Skill instructions](SKILL.md)
- [Case contract](references/case-contract.md)

## Skill Output

可导入官网的 JSON，或经账号授权发布的稳定 ID 案例；包含真实 Input → Prompt →
Output、验收证据、成品图与可选公开 Session。分别报告准备、预检、提交和线上验收状态。

## Skill Version

0.4.0

## Ethical Considerations

只发布用户确认过的脱敏摘要与图片。分享摘要不等于同意上传完整会话；不制造评价、
价格、指标、文件或上线状态。

## LovStudio Evidence

### User Cases

见 [`cases/cases.json`](cases/cases.json)：首案来自创建本 Skill 的真实需求。

### Dimension Map

`skill-card.yaml` 记录 evidence integrity、privacy、mutation safety、paid session
integrity 与 live truthfulness 五个维度及其证据状态。

### Pricing Basis

见 [`pricing-card.yaml`](pricing-card.yaml)。该 Skill 免费，用于提高整个 Skill
目录的案例可信度。

### Distribution

通过 LovStudio 官网与源仓库分发。远端版本、Release 和安装结果须分别核验，
不由本地版本号推断。WorkBuddy 与 SkillPay 不在本次分发范围。
