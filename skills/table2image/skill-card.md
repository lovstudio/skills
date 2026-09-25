# 表格成图 · Table to Image · Skill Card

## Description

将 Markdown 表格与可选 Mable 型号或布局参数转换成托管 PNG 地址，也可下载并校验
本地图片。布局求解和渲染留在 Mable 服务端，Skill 只负责可移植的传输与验收。

## Owner

LovStudio，维护联系地址为 <https://lovstudio.ai>。

## License / Terms

Skill 源码采用 MIT License。Mable API 的可用性、保存期限和服务限制由所选服务端
单独约定。

## Use Case

适合需要把 Markdown 对比表、清单、接口表或结构化摘要转为移动端友好图片的作者、
编辑、Agent、开发者与产品团队。输入是表格和可选布局，核心输出是托管 PNG URL。

## Deployment Geography

可在全球任何具备 Python 3.9+ 且能访问获准 Mable API 的 Agent 环境运行。

## Requirements / Dependencies

- Python 3.9+。
- 可访问的 Mable API。
- 当前接口不要求凭据；不依赖浏览器、字体或 sibling Skill。

## Known Risks and Mitigations

- 表格可能包含私密信息：发送前审查内容；敏感场景改用获准的自托管 API。
- API 可能未部署或暂时不可用：保留 HTTP 状态与响应摘要，不伪造结果。
- 客户端默认参数可能漂移：默认布局不在本地复制，直接交给服务端决定。
- 下载内容可能不是图片：写入前检查 `Content-Type` 与 PNG signature。

## References

- [Machine-readable card](skill-card.yaml)
- [Primary Skill instructions](SKILL.md)
- [Mable API contract](references/api-contract.md)
- [Composition record](references/skill-composition.md)

## Skill Output

返回 JSON，其中包含 `image_url`、`format`、`width`、`height`、`layout_width`、
`model`、`credits_spent` 和 `credits_remaining`。指定本地输出后增加绝对文件路径与
字节数，并保证文件通过 PNG 检查。

## Skill Version

0.1.1

## Ethical Considerations

不得把秘密、受监管或未经允许的数据发送到第三方渲染服务。图片只改变表达方式，
不会提高数据本身的真实性；不得利用视觉包装掩盖错误或误导性数据。

## LovStudio Evidence

### User Cases

[`cases/cases.json`](cases/cases.json) 记录了真实本地 Mable API 的 POST、图片下载和
视觉检查。案例输出为 1520 × 432、66191 bytes 的 PNG。

### Dimension Map

- API contract fidelity：单测检查鉴权请求头、请求字段和八项必需响应元数据。
- Render integrity：真实 PNG 通过内容类型、signature、尺寸与人工视觉检查。
- Diagnostic quality：非表格输入与 HTTP 错误保持明确、可复制的诊断。
- Portability：CLI 仅使用 Python 标准库，配置来自 flag、环境或 Profile。

当前没有把这些证据折算成主观总分；机器卡使用 `null` 明确表示未评分。

### Pricing Basis

本地 Skill 与 CLI 免费；托管渲染、存储、私有部署与 SLA 不在免费承诺内。完整边界
见 [`pricing-card.yaml`](pricing-card.yaml)。

### Distribution

- Local install：已验证。
- GitHub：未发布。
- LovStudio：未发布。
- WorkBuddy / SkillPay：未上传、未发布。
