# Skill Card — lov-repost-wechat-article

## Description

把合作方微信公众号文章转换成一份来源可核验、原文主体冻结、发布方增量清楚的转载稿，并通过既有公众号发布链回读草稿状态。

## Owner

LovStudio — <https://lovstudio.ai>

## License / Terms

Skill 源码采用 MIT。来源文章、图片、Logo、转载许可和公众号发布权限仍由调用者与相应权利人负责。

## Use Case

面向公众号作者、品牌团队和合作运营人员。输入可以是公开微信文章 URL，也可以是可由 `lov-wdb-cli` 缩窄的合作方、标题或日期线索；输出是带来源账本、冻结正文、发布方开场与收尾、品牌资产和远端草稿收据的转载包。

## Requirements

- Python 3.9+ 与 beautifulsoup4
- `lov-branding-consistency`
- `lov-publish-wechat-article`
- 可选 `lov-wdb-cli`
- 远端草稿凭据由下游 `lov-env-management` 处理，不进入本 Skill 源码

## Deployment Geography

面向全球可运行 Portable Agent Skills 的本地桌面或 CLI 环境；微信公众号写入能力取决于目标账号与下游网关权限。

## Known Risks

- 全篇润色破坏来源正文：使用唯一冻结区和文字/图片散列双重核验。
- 私人合作细节外泄：四栏语境账本只允许公开事实进入成品。
- 转载误报原创：`copyrightMode` 固定为 `reprint`，来源账号与完整 URL 原位展示。
- 回读失败后生成重复草稿：先保存 `mediaId` 和远端正文，未诊断前不再次新建。
- 草稿误报公开发布：严格区分 `prepared`、`draft_created` 与 `published`。

## References

- [机器可读 Skill Card](skill-card.yaml)
- [主 Skill 指令](SKILL.md)
- [来源与保真契约](references/source-fidelity.md)
- [真实 S创案例](cases/schuang-2026-evidence.json)

## Skill Output

输出 Markdown、HTML、JSON、JPEG/PNG。`scripts/audit_repost.py` 验证来源块、可见文字 SHA-256、来源 URL、原图数量和增量区块；下游发布收据还必须包含 `remoteFidelityVerified=true`。

## Skill Version

0.1.0

## Ethical Considerations

不伪造转载许可、合作方背书、第一人称经历、原创声明或发布状态；不把内部聊天、联系人、未官宣议题和凭据写入公开制品。

## LovStudio Evidence

## User Cases

[`cases/cases.json`](cases/cases.json) 记录了 `S创上海2026全嘉宾Loading…100%` 的真实 Input → Prompt → Output；[`cases/schuang-2026-evidence.json`](cases/schuang-2026-evidence.json) 保存去隐私化的本地与远端验收数据。

### Dimension Map

机器可读卡覆盖来源可追溯、原文保真、编辑分离、隐私与权利、远端状态五个维度；不填写没有可比基准的虚构分数。

## Pricing Basis

本地 Skill 免费，价值边界是可审计的转载流程、保真脚本和组合契约；不包含模型调用、素材许可、账号、人工审核或代发布服务。加入托管抓取、版权许可和多账号审批后复评。

## Distribution

本地版本免费。当前仅 `local: available`，GitHub、LovStudio、WorkBuddy 和 SkillPay 均未发布或准备，不把本地安装写成渠道上线。
