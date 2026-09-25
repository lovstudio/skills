# 飞书文档同步 · Feishu Doc Sync · Skill Card

## Description

将本地 Markdown 同步为指定飞书知识库文档，并通过新的远端读取验证正文、知识库位置和链接权限。

## Owner

- Team: LovStudio
- Contact: https://lovstudio.ai

## License / Terms

MIT。可在保留许可证的前提下使用和修改；飞书账号、内容和权限仍受用户所在租户政策约束。

## Use Case

- Audience: 以 Markdown 为本地真源，并需要同步到飞书知识库的团队与创作者。
- Supported input: 本地 Markdown、知识空间名称或 ID、同名冲突策略、链接权限档位。
- Expected task: 创建或更新 Wiki 文档，并拿到可复核的内容、位置与权限证据。

## Deployment Geography

global。运行于安装了 `lark-cli`、Python 3.8+ 且已有飞书 user 授权的本地 Agent 环境。

## Requirements / Dependencies

- `lark-cli` 与可访问目标知识空间的 user 身份。
- Python 3.8+。
- `lov-branding-consistency`。
- 凭据由 `lark-cli` 管理，不进入 Skill 源码、参数收据或案例文件。

## Known Risks and Mitigations

1. 同名文档重复或进入错误空间：完整枚举知识空间与目标层级，要求明确冲突策略，写后回读节点。
2. Markdown 被平台规范化或丢失：写后重新获取全文，核对标题、章节、表格、链接、引用和关键文本。
3. 链接权限公开过宽：只映射用户明确选择的档位，检查 `manage_public`，并对底层 Docx 设置后重新读取。
4. API 权限与匿名访问混淆：分别报告 `anyone_readable` API 回读和无登录态访问结果。

## References

- [Primary Skill instructions](SKILL.md)
- [Machine-readable card](skill-card.yaml)
- [Skill composition](references/skill-composition.md)
- [User Profile contract](references/user-profile.md)

## Skill Output

- Type: 已核验的飞书 Wiki 文档与发布收据。
- Format: Feishu Docx、Wiki URL、JSON evidence。
- Parameters: Markdown source、Wiki target、conflict policy、link access、optional lark-cli profile。
- Validation: fresh node read、full content fetch、fresh public-permission read。
- Version: 0.1.0。

## Skill Version

0.1.0

## Ethical Considerations

不发布内部上下文、凭据或无关私人信息。互联网链接权限必须由用户明确选择。不得把 API 写入成功描述为内容与权限均已完成，也不得把 `anyone_readable` 自动夸大为无需登录匿名访问。

## LovStudio Evidence

### User Cases

真实案例见 [`cases/cases.json`](cases/cases.json) 与 [`cases/2026-08-30-ai-camp-plan-receipt.json`](cases/2026-08-30-ai-camp-plan-receipt.json)。

### Dimension Map

| Dimension | Evidence |
|---|---|
| Source fidelity | 远端回读数量与关键文本全部通过；两个未发布的本地相对链接明确记录为纯文本降级。 |
| Target accuracy | 节点回读确认目标空间、根节点、标题与底层 Docx。 |
| Permission accuracy | fresh read 返回 `external_access=true`、`link_share_entity=anyone_readable`。 |
| Status integrity | 收据区分创建、迁入 Wiki、内容核验、权限核验与匿名访问限制。 |

### Pricing Basis

见 [`pricing-card.yaml`](pricing-card.yaml)。本地 Skill 免费；不包含托管、批量迁移或企业权限策略自动化。

### Distribution

Free channels: local。Paid channels: none。尚未发布到远端仓库、catalog 或 marketplace。
