# Jessy 名片设计 · Jessy Card Design · Skill Card

## Description
克隆 Jessy 那张横版机构名片的版式与信息层级，做一张当前主体自己的双面名片。身份全部换成主体的：品牌色、官方 Logo、确认过的联系方式、自己的二维码和据点线稿。
## Owner
lovstudio；由本地 Skill 真源维护，不承诺支持 SLA。
## License / Terms
代码与说明 MIT。案例中的手工川、Lovstudio.AI 标识与二维码只作本地证据；Jessy 的原名片不随源码保存，其机构标识与主色不属于本版式。
## Use Case
想用 Jessy 那张名片的横版结构做自己或团队的名片；资料与品牌资产已在本地。
## Deployment Geography
全球本地 Agent 运行，需要 Python 与 headless Chrome。
## Requirements / Dependencies
Python 3.9+ 标准库，Chrome、Chromium 或 Edge。可选 ImageMagick 7（线稿）、opencv-python（二维码）、OPENROUTER_API_KEY（生成线稿）。品牌门禁为 lov-branding-consistency。
## Known Risks and Mitigations
Jessy 身份残留：版式与身份逐项分开，主色换成主体 Logo 色，模板只带中性素材。编造资料：每个槽位登记来源，没有就删行。第三方隐私：不需要也不保存原图。二维码失效：不小于 140 px，四个尺度回读并比对源载荷。线稿带字：只生成无字线稿并看图。
## References
[Instructions](SKILL.md)、[Jessy layout](references/jessy-style.md)、[Layout spec](references/layout-spec.md)、[Case](cases/cases.json)。
## Skill Output
正面、背面 PNG（默认 3240 × 1944），正反拼图 PNG，内嵌全部素材的 HTML，以及 JSON 渲染报告。屏幕用 RGB，不含印刷出血。
## Skill Version
0.2.0
## Ethical Considerations
只为用户本人或其授权的主体做名片；不用 Jessy 或其机构的身份；不保存第三方名片；不编造履历与联系方式；随附消息只起草不发送。
## User Cases
2026-11-18 按 Jessy 名片版式做手工川名片：用户看过成品回复“挺好的”；作者本机按 card.json 回放与当日交付逐像素一致，交付图二维码四个尺度均解码。公开副本的个人微信二维码换成了占位图。详见 cases/cases.json。没有用户评分或第三方质量评分。
## Dimension Map
版式还原、身份与事实、二维码可用、可复现渲染、主体可替换五项，证据见 skill-card.yaml；评分均为空。
## Pricing Basis
免费本地复用；图像 API、字体授权、印刷与定制设计不包含在内。增加印刷输出或托管服务后重评。
## Distribution
本机共享入口与宿主链接已建立；源码在 GitHub 私有仓库，公开副本由 lovstudio/skills 镜像提供。lovstudio 官网：live（2026-11-18：lovstudio/skills#84 合并（e2946ab），站点读到该提交；lovstudio.ai/skills/jessy-style-card-design 返回 200 并显示 0.2.0；隔离目录 npx lovstudio skills add jessy-style-card-design --project 装上 0.2.0（含依赖 lov-branding-consistency），装好的副本渲染模板无版式问题。lovstudio.cn 待国内镜像任务同步。）
