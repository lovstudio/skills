# Skill Card — lov-media-crawler

## Description

把一个已知的公开视频或社交媒体内容链接解析为经过容器与大小检查的本地媒体文件，并附带下载速度、来源和诊断 JSON。

## Owner

LovStudio Skills · `maintainers@lovstudio.com`

## License / Terms

本 Skill 自有代码使用 MIT。可选 MediaCrawler checkout 继续受其 `NON-COMMERCIAL LEARNING LICENSE 1.1` 约束；平台条款与媒体版权不因下载而改变。

## Use Case

面向需要保存自己或已获授权社交媒体内容的创作者、研究者和 Agent。输入是一条视频号或 MediaCrawler 支持平台链接，输出为源媒体文件和 JSON 验证报告。

## Deployment Geography

本地优先、全球可移植。视频号一键授权目前优先支持 macOS Keychain；环境变量模式可跨平台。

## Requirements / Dependencies

- Python 3.9+ 与 curl。
- aria2、ffprobe 为推荐可选依赖。
- 视频号首次授权可选 Playwright 与 Chrome。
- MediaCrawler 路径可选 Git、uv、Node.js 与固定版本的上游 checkout。

## Known Risks and Mitigations

- 平台 API 或登录态变化：解析与下载解耦，失败返回稳定错误码和重新授权命令。
- 版权与访问限制：只处理用户有权访问和保存的内容，不绕过 DRM、付费、私密或地域控制。
- 第三方解析隐私：公共 Worker 默认关闭，只有明确 opt-in 才发送公开分享链接。

## References

- [Machine-readable card](skill-card.yaml)
- [Primary Skill instructions](SKILL.md)
- [Platform matrix](references/platform-matrix.md)
- [Upstream and licenses](references/upstream-and-licenses.md)

## Skill Output

原始视频或图片文件，以及包含状态、平台、去查询参数来源、路径、字节数、耗时、平均速度、验证结果与 `context_id` 的 JSON。默认不转码。

## Skill Version

0.1.0

## Ethical Considerations

按人工使用规模运行，不做账号级批量抓取。Cookie、Token 与签名 CDN 查询参数不进入 Profile、报告或对话输出。

## LovStudio Evidence

### User Cases

见 [`cases/cases.json`](cases/cases.json)。案例包含实际输入、最小 Prompt、输出与验证状态。

### Dimension Map

- 下载正确性：4/5，容器魔数、大小与可选 ffprobe 检查。
- 平台可达性：3/5，示例视频号链接的公开元数据已验证，完整视频仍需一次用户授权。
- 下载效率：4/5，aria2 多连接优先，curl 可续传兜底。

### Pricing Basis

见 [`pricing-card.yaml`](pricing-card.yaml)。本地胶水代码免费；不包含托管解析 SLA、商业 MediaCrawler 授权或媒体权利。

### Distribution

当前仅完成本地创建、验证与安装；未声明 GitHub、LovStudio、WorkBuddy 或 SkillPay 已发布。
