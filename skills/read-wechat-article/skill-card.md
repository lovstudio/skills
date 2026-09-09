# 公众号文章读取器 · WeChat Article Reader · Skill Card

## Description

把公开微信公众号文章 URL 转为本地可编辑 Markdown。文字型文章直接提取正文；
图片型文章下载原图、执行中文 OCR，并由代理逐图核对后按章节整理。输出保留
标题、账号、发布时间、原图目录、来源链接和原文表述。

## Owner

contributors，联系地址为 https://github.com/lovstudio/skills。

## License

源码按 MIT 许可使用。整理稿中的原文、图片、商标和版权归原作者。

## Use Case

面向需要把公开公众号文章归档、转写或二次引用的人。用户提供一条公开
`mp.weixin.qq.com` 文章 URL，得到本地 Markdown、原图和 JSON 清单。

## Deployment Geography

全球，本地运行。需要访问公开微信文章页面。

## Requirements / Dependencies

- Python 3.8+
- PyYAML（用于质量门验证）
- 网络访问
- macOS Vision，或带 `chi_sim` 的 Tesseract
- 可选：Xcode Command Line Tools
- `lov-branding-consistency`

不需要 Cookie、Token、付费账号或远端 API。

## Known Risks and Mitigations

- 页面需要登录、验证或地域限制：停止并报告，不绕过访问控制。
- OCR 误识别：逐图视觉核对，不明确处保留原图并在备注中标明。
- 原文前后不一致：按原文保留，在“原文备注”中记录差异。
- 版权和转载边界：保留来源、公众号和原图，不声明拥有原文版权。

## References

- [Machine-readable card](skill-card.yaml)
- [Primary Skill instructions](SKILL.md)
- [WeChat extraction notes](references/wechat-extraction.md)

## Skill Output

一个可离线阅读的 Markdown，配套：

- `manifest.json`
- `images/` 原图目录
- 图片型文章附 OCR 草稿
- 原文备注

## Skill Version

0.1.0

## Ethical Considerations

只能处理用户有权访问和保存的公开内容。保留来源与署名，不绕过登录、付费、
私密或地域限制；不把整篇受版权保护内容擅自重新发布为原创。

## LovStudio Evidence

### User Cases

见 [`cases/cases.json`](cases/cases.json)。真实案例是一条图片型公众号文章，
输出为本地 Markdown、13 张原图、manifest 和 OCR 草稿。

### Dimension Map

机器可读卡包含来源保真、完整度和可移植性三个维度，每条都有真实案例证据。

### Pricing Basis

免费。价值在于免去重复编写公开文章抓取、图片保留、OCR 和来源保真整理流程；
不包含远程发布、付费内容访问、视频下载或商业授权代理。

### Distribution

当前仅本地安装。`github` 和 `lovstudio` 远程渠道尚未发布，计划后续通过
`lov-skill-publisher` 处理。
