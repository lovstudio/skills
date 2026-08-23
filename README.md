<h1 align="center">Lovstudio Skills</h1>

<p align="center">
  <strong>Lovstudio Claude Code AI 编程技能生态的总索引。</strong><br>
  <sub>由 <a href="https://lovstudio.ai">Lovstudio</a> 出品 · <a href="https://agentskills.io">agentskills.io</a></sub>
</p>

<p align="center">
  <b>简体中文</b> · <a href="README.en.md">English</a>
</p>

<p align="center">
  <a href="#技能列表">技能</a> ·
  <a href="#安装">安装</a> ·
  <a href="#工作原理">工作原理</a> ·
  <a href="#贡献">贡献</a> ·
  <a href="#许可证">许可证</a>
</p>

---

## 这是什么

本仓库是 Lovstudio 技能生态的**统一总索引**，所有可发现的 Skill 都从这里汇总。
Skill 的实际内容有两种组织方式：直接放在本仓库的 `skills/<name>/` 中，或维护在
`lovstudio/{name}-skill` 这样的独立仓库中。

本仓库包含：

- [`skills.yaml`](skills.yaml) — 机器可读清单。每个技能包含两类描述：`description` 是给 Agent 看的英文触发文案，由 CI 自动从各自 GitHub 仓库 description 同步；`tagline_en` / `tagline_zh` 是给人看的中英文一句话简介，由维护者手工填写，也就是下方表格里展示的那一列。
- [`README.md`](README.md) / [`README.en.md`](README.en.md) — 由清单自动渲染生成。
- [`skills/`](skills) — 面向安装器的同步镜像。免费技能从各自独立仓库同步而来，付费技能只放可公开分发的加密包或占位内容；真正的源码和历史仍以各自 skill repo 为准。

标记为 ![Free](https://img.shields.io/badge/Free-green) 的技能可以直接安装和使用。标记为 ![Paid](https://img.shields.io/badge/Paid-blueviolet) 的技能需要登录并用 Credits 兑换；安装器只下载加密包，兑换成功后才会按账户权益解密使用。购买或咨询请扫码关注公众号 **手工川**：

<p align="center">
  <img src="assets/shougongchuan-banner.jpg" alt="关注公众号「手工川」获取付费技能" width="720">
</p>

## 技能列表

<!-- COUNT:START -->
> **84 个技能** — 70 个免费 + 14 个付费。
<!-- COUNT:END -->

<!-- SKILLS:START -->
| | 英文名 | 中文名 | 描述 |
|---|---|---|---|
| **通用** | | | |
| ![Free](https://img.shields.io/badge/Free-green) | [`china-website-filing`](https://github.com/lovstudio/china-website-filing-skill) | [中国网站备案](https://github.com/lovstudio/china-website-filing-skill) | 把中国大陆网站从备案准备推进到 ICP、域名上线、公安联网备案与合规巡检，并保留权威证据链。 |
| ![Free](https://img.shields.io/badge/Free-green) | [`describe-image`](https://github.com/lovstudio/describe-image-skill) | [图片描述](https://github.com/lovstudio/describe-image-skill) | 给纯文本模型"看图"：用免费视觉模型把任意图片转成文字描述。 |
| ![Free](https://img.shields.io/badge/Free-green) | [`fact-check`](https://github.com/lovstudio/fact-check-skill) | [事实校验](https://github.com/lovstudio/fact-check-skill) | 用尽调思路确认事实：查一手资料、找反例、标证据等级，给出置信度和下一步。 — 相关: `image-translation-errata` |
| ![Free](https://img.shields.io/badge/Free-green) | [`hanzi-lens`](https://github.com/lovstudio/hanzi-lens-skill) | [汉字镜](https://github.com/lovstudio/hanzi-lens-skill) | 用证据看懂一个汉字：读音、字形、字书、经典语境与专业信息图。 — 依赖: `professional-infographic` |
| ![Free](https://img.shields.io/badge/Free-green) | [`image-creator`](https://github.com/lovstudio/image-creator-skill) | [图像工坊](https://github.com/lovstudio/image-creator-skill) | 按需选择最合适的出图方式：端到端 AI、代码渲染或提示词精修。 — 相关: `professional-infographic`, `professional-portrait`, `image-translation-errata` |
| ![Free](https://img.shields.io/badge/Free-green) | [`image-translation-errata`](https://github.com/lovstudio/image-translation-errata-skill) | [图片翻译勘误](https://github.com/lovstudio/image-translation-errata-skill) | 保留错误机翻的证据，用校样式删改给出正确译文，同时尽量不动原图布局。 — 相关: `translation-review`, `image-creator`, `fact-check` |
| ![Free](https://img.shields.io/badge/Free-green) | [`macos-disk-optimizer`](https://github.com/lovstudio/macos-disk-optimizer-skill) | [Mac 磁盘优化](https://github.com/lovstudio/macos-disk-optimizer-skill) | 按目标容量整理 Mac 磁盘，支持归档迁移、精确回收回滚项，并以真实可用空间完成验收。 |
| ![Free](https://img.shields.io/badge/Free-green) | [`media-crawler`](https://github.com/lovstudio/media-crawler-skill) | [媒体链接下载](https://github.com/lovstudio/media-crawler-skill) | 将有权保存的视频号等社交媒体链接变成可验证的本地媒体文件与诊断报告。 |
| ![Free](https://img.shields.io/badge/Free-green) | [`media-fetch`](https://github.com/lovstudio/media-fetch-skill) | [媒体抓取](https://github.com/lovstudio/media-fetch-skill) | 检索并选择合适版本，qBittorrent 与 aria2 续传兜底，最后验收本地媒体与字幕状态。 |
| ![Free](https://img.shields.io/badge/Free-green) | [`personal-vocabulary`](https://github.com/lovstudio/personal-vocabulary-skill) | [personal-vocabulary](https://github.com/lovstudio/personal-vocabulary-skill) | 一份可跨语音输入法复用的个人词汇表。 |
| ![Paid](https://img.shields.io/badge/Paid-blueviolet) | [`subtitle-freedom`](https://github.com/lovstudio/subtitle-freedom-skill) | [人人字幕](https://github.com/lovstudio/subtitle-freedom-skill) | 以用户选定级别为最低难度线生成英语学习字幕，覆盖更高难度表达，并可选生成不剧透人物卡片与不烧录视频的 ASS/PGS 水印外置字幕。 |
| ![Paid](https://img.shields.io/badge/Paid-blueviolet) | [`wdb-cli`](https://github.com/lovstudio/wdb-cli-skill) | [万能微信秘钥](https://github.com/lovstudio/wdb-cli-skill) | 自动发现 WDB Pro 管理密钥，精准读取聊天、联系人、朋友圈、结构与稳定记录。 |
| **商务** | | | |
| ![Free](https://img.shields.io/badge/Free-green) | [`bp`](https://github.com/lovstudio/bp-skill) | [BP 工具包](https://github.com/lovstudio/bp-skill) | 可组合的投资人 BP 工具包：大纲、PPT 制作、审稿润色既能单独使用，也能串成完整流程。 — 依赖: `bp-outline`, `bp-deck`, `bp-polish` |
| ![Free](https://img.shields.io/badge/Free-green) | [`bp-deck`](https://github.com/lovstudio/bp-skill) | [BP 幻灯片](https://github.com/lovstudio/bp-skill) | 把已经确认的 BP 大纲做成风格统一、图表专业的 PPTX、PDF 和全稿预览。 — 依赖: `any2deck` |
| ![Free](https://img.shields.io/badge/Free-green) | [`bp-outline`](https://github.com/lovstudio/bp-skill) | [BP 大纲](https://github.com/lovstudio/bp-skill) | 先把项目材料变成证据账本和投资人看得懂的 12–15 页大纲，再决定是否制作 PPT。 |
| ![Free](https://img.shields.io/badge/Free-green) | [`bp-polish`](https://github.com/lovstudio/bp-skill) | [BP 审稿润色](https://github.com/lovstudio/bp-skill) | 给已有 BP 做投资逻辑、证据、文字、图表和视觉体检，输出评分报告与逐页修改，不为好看改事实。 |
| ![Free](https://img.shields.io/badge/Free-green) | [`contract-review-pro`](https://github.com/lovstudio/contract-review-pro-skill) | [合同审阅 · 专业版](https://github.com/lovstudio/contract-review-pro-skill) | 专业级合同审阅 — 四层方法论（主体核验 + 基础 + 业务 + 法务），结构化批注含风险等级，附合同摘要、综合意见与业务流程图。 |
| ![Paid](https://img.shields.io/badge/Paid-blueviolet) | [`event-curator`](https://github.com/lovstudio/event-curator-skill) | [活动策展](https://github.com/lovstudio/event-curator-skill) | 从嘉宾履历一键生成可交付的活动策划案 — 主题文案、分钟级 rundown、主持人问题卡、伴手礼。 |
| ![Free](https://img.shields.io/badge/Free-green) | [`expense-report`](https://github.com/lovstudio/expense-report-skill) | [报销整理](https://github.com/lovstudio/expense-report-skill) | 发票图片或文字一键整理成分类报销 Excel，业务招待、差旅、办公自动归类。 |
| ![Paid](https://img.shields.io/badge/Paid-blueviolet) | [`proposal`](https://github.com/lovstudio/proposal-skill) | [专业需求评估](https://github.com/lovstudio/proposal-skill) | 把项目简述一键变成可交付的商业提案，方案、报价、排版全配齐。 |
| ![Free](https://img.shields.io/badge/Free-green) | [`review-doc`](https://github.com/lovstudio/review-doc-skill) | [合同审阅 · 日常版](https://github.com/lovstudio/review-doc-skill) | 审阅文档或合同，输出带批注的 docx，直接拿给同事或客户。 |
| ![Free](https://img.shields.io/badge/Free-green) | [`solution-architect`](https://github.com/lovstudio/solution-architect-skill) | [解决方案架构师](https://github.com/lovstudio/solution-architect-skill) | 把产品或技术需求转成有调研依据、开源优先的可执行解决方案。 |
| **设计** | | | |
| ![Free](https://img.shields.io/badge/Free-green) | [`business-card`](https://github.com/lovstudio/business-card-skill) | [专业名片生成](https://github.com/lovstudio/business-card-skill) | 把任何人的姓名、头衔、金句一键变成精美的编辑式名片，输出高清 PNG 与可点击下载的 HTML。 |
| ![Paid](https://img.shields.io/badge/Paid-blueviolet) | [`event-poster`](https://github.com/lovstudio/event-poster-skill) | [大师级海报生成](https://github.com/lovstudio/event-poster-skill) | 把活动信息一键变成高质感海报，可直接分享或用于线下展览。 |
| ![Free](https://img.shields.io/badge/Free-green) | [`find-logo`](https://github.com/lovstudio/find-logo-skill) | [Logo 狩猎](https://github.com/lovstudio/find-logo-skill) | 按品牌名或网址抓取 logo，自动评分择优（偏好长条形 + 透明底），统一归档到本地，方便网站/PPT/海报罗列。 |
| ![Free](https://img.shields.io/badge/Free-green) | [`maintain-partners`](https://github.com/lovstudio/maintain-partners-skill) | [合作伙伴维护](https://github.com/lovstudio/maintain-partners-skill) | 一键抓取品牌 logo、标准化处理并接入官网 partners 区块，多语言全覆盖。 — 依赖: `find-logo` |
| ![Paid](https://img.shields.io/badge/Paid-blueviolet) | [`oh-my-landingpage`](https://github.com/lovstudio/oh-my-landingpage-skill) | [品牌着陆页](https://github.com/lovstudio/oh-my-landingpage-skill) | 从产品与品牌事实出发，独立推导适合当前产品的叙事与视觉，并完成实现、响应式和生产回读。 |
| ![Paid](https://img.shields.io/badge/Paid-blueviolet) | [`professional-infographic`](https://github.com/lovstudio/professional-infographic-skill) | [专业信息图](https://github.com/lovstudio/professional-infographic-skill) | 把复杂材料或投资路径重构为一条可回溯的视觉论证，从进入、分阶段退出到最终判断。 — 相关: `image-creator` |
| ![Free](https://img.shields.io/badge/Free-green) | [`professional-portrait`](https://github.com/lovstudio/professional-portrait-skill) | [职业形象照](https://github.com/lovstudio/professional-portrait-skill) | 把一张普通人像修成干净、自然、仍然像本人的职业形象照。 — 相关: `image-creator` |
| ![Paid](https://img.shields.io/badge/Paid-blueviolet) | [`visual-clone`](https://github.com/lovstudio/visual-clone-skill) | [像素级海报复刻](https://github.com/lovstudio/visual-clone-skill) | 从参考图中提取设计要素，生成可复刻同款风格的指令。 |
| **学术** | | | |
| ![Paid](https://img.shields.io/badge/Paid-blueviolet) | [`academic-translator`](https://github.com/lovstudio/academic-translator-skill) | [论文 PDF 超级翻译官](https://github.com/lovstudio/academic-translator-skill) | 将英文论文译为中文，优先保留图表、公式、页码对应与目录跳转。 — 售价 ¥4.99 |
| ![Paid](https://img.shields.io/badge/Paid-blueviolet) | [`paper-translator`](https://github.com/lovstudio/paper-translator-skill) | [论文超级翻译官](https://github.com/lovstudio/paper-translator-skill) | 将英文论文译为中文 PDF，支持同页数、对照页与段落双语，并在保版式路线中保留图表和公式。 — 售价 ¥4.99 |
| ![Free](https://img.shields.io/badge/Free-green) | [`thesis-polish`](https://github.com/lovstudio/thesis-polish-skill) | [论文润色](https://github.com/lovstudio/thesis-polish-skill) | MBA 论文全维度润色，对标国优标准，打磨语言、结构、论证与创新四个面。 |
| ![Free](https://img.shields.io/badge/Free-green) | [`translation-review`](https://github.com/lovstudio/translation-review-skill) | [译文审阅](https://github.com/lovstudio/translation-review-skill) | 中译英译文审阅，从六个维度逐条对照原文，找出问题并给出改写建议。 — 相关: `image-translation-errata` |
| **办公** | | | |
| ![Free](https://img.shields.io/badge/Free-green) | [`any2deck`](https://github.com/lovstudio/any2deck-skill) | [万物转幻灯](https://github.com/lovstudio/any2deck-skill) | 把任意内容变成带设计感的幻灯片，16 种风格可选，导出 PPTX / PDF。 — 相关: `any2pdf`, `any2docx` |
| ![Free](https://img.shields.io/badge/Free-green) | [`any2docx`](https://github.com/lovstudio/any2docx-skill) | [万物转 Word](https://github.com/lovstudio/any2docx-skill) | 把 Markdown 转成排版规范的 Word 文档，可以直接发给甲方。 — 相关: `any2pdf`, `any2deck` |
| ![Free](https://img.shields.io/badge/Free-green) | [`any2pdf`](https://github.com/lovstudio/any2pdf-skill) | [万物转 PDF](https://github.com/lovstudio/any2pdf-skill) | 把 Markdown 排成出版级 PDF，支持中英混排、代码与表格；新增宋黑阅读，共 16 套主题。 — 相关: `any2docx`, `any2deck` |
| ![Free](https://img.shields.io/badge/Free-green) | [`fill-form`](https://github.com/lovstudio/fill-form-skill) | [表单代笔](https://github.com/lovstudio/fill-form-skill) | 自动填写 Word 表单模板，字段识别 + 中英文排版一气呵成。 |
| ![Free](https://img.shields.io/badge/Free-green) | [`fill-web-form`](https://github.com/lovstudio/fill-web-form-skill) | [网页代笔](https://github.com/lovstudio/fill-web-form-skill) | 用你本地的知识库来应答网页表单，一轮检索一轮生成，草稿即交付。 |
| ![Free](https://img.shields.io/badge/Free-green) | [`pdf2png`](https://github.com/lovstudio/pdf2png-skill) | [PDF 出长图](https://github.com/lovstudio/pdf2png-skill) | 把 PDF 拼成一张长图 PNG，在 macOS 上快到几乎瞬间出图。 |
| ![Free](https://img.shields.io/badge/Free-green) | [`png2svg`](https://github.com/lovstudio/png2svg-skill) | [PNG 矢量化](https://github.com/lovstudio/png2svg-skill) | 把 PNG 矢量化为高质量 SVG，自动抠背景、曲线平滑。 |
| ![Free](https://img.shields.io/badge/Free-green) | [`rich-export`](https://github.com/lovstudio/rich-export-skill) | [富媒体一键导出](https://github.com/lovstudio/rich-export-skill) | 一份富媒体内容，同时交付网页、可编辑文档、打印版和归档包。 |
| ![Free](https://img.shields.io/badge/Free-green) | [`yoda-automation`](https://github.com/lovstudio/yoda-automation-skill) | [Yoda 自动化](https://github.com/lovstudio/yoda-automation-skill) | 把一次性提醒和周期跟进变成可核验的 Yoda 原生自动化，带时区、运行证据、去重与完成后停用。 |
| **内容创作** | | | |
| ![Free](https://img.shields.io/badge/Free-green) | [`anti-wechat-ai-check`](https://github.com/lovstudio/anti-wechat-ai-check-skill) | [文章去 AI 味](https://github.com/lovstudio/anti-wechat-ai-check-skill) | 检测文章的 AI 味并做人性化润色，帮助稳过微信 3.27 条款的机器判定。 |
| ![Free](https://img.shields.io/badge/Free-green) | [`deep-research`](https://github.com/lovstudio/deep-research-skill) | [深度研究](https://github.com/lovstudio/deep-research-skill) | 生成带引用追踪、证据留存和主张校验的深度研究报告，并输出 Markdown/HTML/PDF。 |
| ![Free](https://img.shields.io/badge/Free-green) | [`document-illustrator`](https://github.com/lovstudio/document-illustrator-skill) | [文档配图](https://github.com/lovstudio/document-illustrator-skill) | 给长文原地配图，先规划插入点再并行出图，最后自动插回原文。 — 依赖: `image-creator` |
| ![Free](https://img.shields.io/badge/Free-green) | [`style-clone`](https://github.com/lovstudio/style-clone-skill) | [文风克隆](https://github.com/lovstudio/style-clone-skill) | 从样本文章中提取文风画像，再把任意内容改写成该文风。 |
| ![Paid](https://img.shields.io/badge/Paid-blueviolet) | [`wechat-article-branding`](https://github.com/lovstudio/wechat-article-branding-skill) | [公众号文章品牌化](https://github.com/lovstudio/wechat-article-branding-skill) | 把现有公众号文章加工成结构清晰、艺术封面统一、Logo 居中、封面 Prompt 可复用且经过真实页面验收的品牌化成品。 — 相关: `wechat-article-operator` |
| ![Paid](https://img.shields.io/badge/Paid-blueviolet) | [`wechat-article-operator`](https://github.com/lovstudio/wechat-article-operator-skill) | [公众号文章操作器](https://github.com/lovstudio/wechat-article-operator-skill) | 可靠读取、编辑、保存并重载验收现有公众号文章，支持精确内容修改与封面替换。 — 相关: `wechat-article-branding` |
| ![Paid](https://img.shields.io/badge/Paid-blueviolet) | [`write-professional-book`](https://github.com/lovstudio/write-professional-book-skill) | [专业写书](https://github.com/lovstudio/write-professional-book-skill) | 从大纲开始，逐章写出一本完整的书，技术、教程、专著多种风格。 |
| ![Paid](https://img.shields.io/badge/Paid-blueviolet) | [`wxmp-cracker`](https://github.com/lovstudio/wxmp-cracker-skill) | [公众号神器](https://github.com/lovstudio/wxmp-cracker-skill) | 把微信公众号的文章批量归档成可再利用的整洁文本。 |
| **开发工具** | | | |
| ![Free](https://img.shields.io/badge/Free-green) | [`app-generator`](https://github.com/lovstudio/app-generator-skill) | [App 生成器](https://github.com/lovstudio/app-generator-skill) | 按需求生成 Lovstudio 级 web、PWA 或 Tauri App，内置品牌、UI、数据层、部署/发布和开发辅助。 |
| ![Free](https://img.shields.io/badge/Free-green) | [`ataru-indexing`](https://github.com/lovstudio/ataru-indexing-skill) | [Ataru 索引](https://github.com/lovstudio/ataru-indexing-skill) | 在检索之前，先确认本机的 AI 会话记忆真的可被搜索。 |
| ![Free](https://img.shields.io/badge/Free-green) | [`ataru-search`](https://github.com/lovstudio/ataru-search-skill) | [Ataru 检索](https://github.com/lovstudio/ataru-search-skill) | 把你和 AI 已经想清楚的事找回来，并读回它原本的上下文。 |
| ![Free](https://img.shields.io/badge/Free-green) | [`auto-context`](https://github.com/lovstudio/auto-context-skill) | [上下文体检](https://github.com/lovstudio/auto-context-skill) | 监测 Claude Code 上下文是否被污染，适时提示你 /fork 或 /btw。 |
| ![Free](https://img.shields.io/badge/Free-green) | [`cc-migrate-session`](https://github.com/lovstudio/cc-migrate-session) | [会话迁移](https://github.com/lovstudio/cc-migrate-session) | 项目目录搬家后，让 Claude Code 的历史会话还能正常 `--resume`。 |
| ![Free](https://img.shields.io/badge/Free-green) | [`clash-tun-doctor`](https://github.com/lovstudio/clash-tun-doctor-skill) | [Clash TUN 网络医生](https://github.com/lovstudio/clash-tun-doctor-skill) | 从最终运行态和日志诊断 Clash TUN 故障，执行可回滚修复并验证真实应用链路。 |
| ![Free](https://img.shields.io/badge/Free-green) | [`deploy-to-vercel`](https://github.com/lovstudio/deploy-to-vercel-skill) | [部署到 Vercel](https://github.com/lovstudio/deploy-to-vercel-skill) | 一键把前端部署到 Vercel，自动配好 Cloudflare DNS 和自定义域名。 |
| ![Free](https://img.shields.io/badge/Free-green) | [`dsh-plugin-creator`](https://github.com/lovstudio/dsh-plugin-creator-skill) | [DSH 插件开发](https://github.com/lovstudio/dsh-plugin-creator-skill) | 端到端开发 DSH 插件：选扩展点、搭脚手架、实现并通过仓库门槛。 — 相关: `dsh-plugin-publisher` |
| ![Free](https://img.shields.io/badge/Free-green) | [`dsh-plugin-publisher`](https://github.com/lovstudio/dsh-plugin-publisher-skill) | [DSH 插件发布](https://github.com/lovstudio/dsh-plugin-publisher-skill) | 把已验证的 DSH 插件发布到 npm/git/tarball 渠道，并逐一核验可加载。 — 相关: `dsh-plugin-creator` |
| ![Free](https://img.shields.io/badge/Free-green) | [`electron-app-relaunch`](https://github.com/lovstudio/electron-app-relaunch-skill) | [Electron 应用重启](https://github.com/lovstudio/electron-app-relaunch-skill) | 为 Electron 实现真正的完整应用重启，并清晰区分界面刷新与更新交接。 |
| ![Free](https://img.shields.io/badge/Free-green) | [`electron-delta-updater`](https://github.com/lovstudio/electron-delta-updater-skill) | [Electron 增量更新](https://github.com/lovstudio/electron-delta-updater-skill) | 为 Electron 应用建立可验证的增量自动更新，覆盖 Sparkle、appcast、签名与真实安装验证。 |
| ![Free](https://img.shields.io/badge/Free-green) | [`finder-action`](https://github.com/lovstudio/finder-action-skill) | [访达右键动作](https://github.com/lovstudio/finder-action-skill) | 几分钟给 macOS 访达右键菜单加一个你自己的动作。 |
| ![Free](https://img.shields.io/badge/Free-green) | [`gh-access`](https://github.com/lovstudio/gh-access-skill) | [GitHub 协作者管理](https://github.com/lovstudio/gh-access-skill) | 一条命令给私有 GitHub 仓库加减协作者权限，或盘点现有访问清单。 |
| ![Free](https://img.shields.io/badge/Free-green) | [`gh-contribute`](https://github.com/lovstudio/gh-contribute-skill) | [GitHub 投稿 PR](https://github.com/lovstudio/gh-contribute-skill) | 给任意上游 GitHub 仓库提一份干净的 PR——fork、分支、推送、开 PR 一站搞定。 |
| ![Free](https://img.shields.io/badge/Free-green) | [`gh-tidy`](https://github.com/lovstudio/gh-tidy-skill) | [GitHub 仓库整理](https://github.com/lovstudio/gh-tidy-skill) | 一次过清理 GitHub 上的 issue、PR、分支和标签，让仓库重新整洁。 |
| ![Free](https://img.shields.io/badge/Free-green) | [`install-ai`](https://github.com/lovstudio/install-ai-skill) | [AI 功能初始化](https://github.com/lovstudio/install-ai-skill) | 为 App 初始化可上线的 AI 功能，支持 Agent Client、MaaS、模型偏好和配套 UI。 |
| ![Free](https://img.shields.io/badge/Free-green) | [`install-tanstack-query`](https://github.com/lovstudio/install-tanstack-query-skill) | [TanStack Query 初始化](https://github.com/lovstudio/install-tanstack-query-skill) | 初始化 TanStack Query，并把分散的请求状态收敛到统一 query keys 和 hooks。 |
| ![Free](https://img.shields.io/badge/Free-green) | [`integrate-lovinsp`](https://github.com/lovstudio/integrate-lovinsp-skill) | [Lovinsp 集成](https://github.com/lovstudio/integrate-lovinsp-skill) | 开发时点击页面元素直达源码。 |
| ![Free](https://img.shields.io/badge/Free-green) | [`mobile-adapt`](https://github.com/lovstudio/mobile-adapt-skill) | [移动端适配](https://github.com/lovstudio/mobile-adapt-skill) | 扫描并修复 Web 项目的移动端适配问题——溢出、安全区、视口单位、响应式布局和多级导航。 |
| ![Free](https://img.shields.io/badge/Free-green) | [`npm-publisher`](https://github.com/lovstudio/lov-npm-publisher-skill) | [npm 发布器](https://github.com/lovstudio/lov-npm-publisher-skill) | 自动发布 npm 包，无需重复登录——OIDC trusted publishing 或本地 NPM_TOKEN。 |
| ![Free](https://img.shields.io/badge/Free-green) | [`obsidian-reset-cache`](https://github.com/lovstudio/obsidian-reset-cache-skill) | [重置 Obsidian 缓存](https://github.com/lovstudio/obsidian-reset-cache-skill) | Obsidian 卡在 Loading cache 时，一键重置缓存救场。 |
| ![Free](https://img.shields.io/badge/Free-green) | [`optimize-tauri-backend`](https://github.com/lovstudio/optimize-tauri-backend-skill) | [Tauri 后端优化](https://github.com/lovstudio/optimize-tauri-backend-skill) | 优化 Tauri 后端结构、命令边界和长 IPC 生命周期，降低 Rust 重启带来的开发摩擦。 |
| ![Free](https://img.shields.io/badge/Free-green) | [`project-port`](https://github.com/lovstudio/project-port-skill) | [项目端口分配](https://github.com/lovstudio/project-port-skill) | 给每个项目分配一个稳定且唯一的开发端口，彻底告别端口撞车。 |
| ![Free](https://img.shields.io/badge/Free-green) | [`release-via-cicd`](https://github.com/lovstudio/release-via-cicd-skill) | [CI/CD 发布](https://github.com/lovstudio/release-via-cicd-skill) | 配置发布流水线、发布新版本，并验证 Tauri/macOS 签名与 notarization 产物。 |
| ![Free](https://img.shields.io/badge/Free-green) | [`repo2docs`](https://github.com/lovstudio/repo2docs-skill) | [文件夹生成文档站](https://github.com/lovstudio/repo2docs-skill) | 把任意文件夹（代码、文章、图片）增量编纂成精美的 Fumadocs 文档站，并部署到 {id}.lovstudio.ai/docs。 |
| ![Free](https://img.shields.io/badge/Free-green) | [`skill-distiller`](https://github.com/lovstudio/skill-distiller-skill) | [Skill 经验蒸馏](https://github.com/lovstudio/skill-distiller-skill) | 将项目经验蒸馏为边界清晰、可创建且可验收的 Skill 蓝图。 |
| ![Free](https://img.shields.io/badge/Free-green) | [`skill-pricing`](https://github.com/lovstudio/skill-pricing-skill) | [Skill 定价](https://github.com/lovstudio/skill-pricing-skill) | 从成本、价值、信心度与渠道适配出发，生成可解释的 Skill Pricing Card。 |
| ![Free](https://img.shields.io/badge/Free-green) | [`skill-publisher`](https://github.com/lovstudio/skill-publisher-skill) | [Skill 发布器](https://github.com/lovstudio/skill-publisher-skill) | 默认自动定价后发布已验证的 Skill，并分别保留各渠道的可核验状态。 — 依赖: `skill-pricing` |
| **Video Creation** | | | |
| ![Free](https://img.shields.io/badge/Free-green) | [`media-creator`](https://github.com/lovstudio/media-creator-skill) | [媒体创作工作流](https://github.com/lovstudio/media-creator-skill) | 把真实录屏整理成可发布成片，保留成果原声，完成 BGM 混音、封面方向和交付质检。 |
| ![Free](https://img.shields.io/badge/Free-green) | [`publish-wechat-channels`](https://github.com/lovstudio/publish-wechat-channels-skill) | [视频号发布器](https://github.com/lovstudio/publish-wechat-channels-skill) | 通过视频号助手发布视频，逐项回读文案、话题、封面与原创状态，并核验最终结果。 |
| ![Free](https://img.shields.io/badge/Free-green) | [`video-chapter`](https://github.com/lovstudio/video-chapter-skill) | [视频章节工作台](https://github.com/lovstudio/video-chapter-skill) | 从字幕确定章节，在 React 工作台调整切点与样式，再导出透明章节条、烧录成片或剪辑软件素材包。 |
| **Meta** | | | |
| ![Free](https://img.shields.io/badge/Free-green) | [`skill-creator`](https://github.com/lovstudio/skill-creator-skill) | [技能脚手架](https://github.com/lovstudio/skill-creator-skill) | 一条命令生成独立版本仓库，并通过 Release 自动同步到聚合分发仓库。 |
| ![Free](https://img.shields.io/badge/Free-green) | [`skill-optimizer`](https://github.com/lovstudio/skill-optimizer-skill) | [技能优化器](https://github.com/lovstudio/skill-optimizer-skill) | 一键体检并修复现有技能，自动升版本号并追加 CHANGELOG。 |
<!-- SKILLS:END -->

<sub>上表由 [`scripts/render-readme.py`](scripts/render-readme.py) 从 [`skills.yaml`](skills.yaml) 自动生成。请编辑 `skills.yaml`，不要手动改表格。</sub>

## 安装

统一使用 `npx lovstudio` 入口：

```bash
# 装单个技能
npx lovstudio skills add any2pdf

# 一次安装全部免费技能；付费技能请逐个兑换
npx lovstudio skills add skills

# 付费技能：登录后确认 Credits 兑换
npx lovstudio skills add proposal
```

免费技能会直接安装。付费技能会先完成登录与 Credits 兑换，再下载加密包；非交互环境请追加
`-y`，例如 `npx lovstudio skills add proposal -y`。

通过 [agentskills.io](https://agentskills.io) 可浏览并一键安装。

## 工作原理

```
lovstudio/skills (本仓库)            ← Lovstudio 技能生态统一总索引
├── README.md                        ← 中文版总索引（默认）
├── README.en.md                     ← English index
└── skills/<name>/                    ← 免费镜像或付费加密分发包

lovstudio/<name>-skill               ← 常规技能的独立源码仓库
├── SKILL.md                         ← 技能定义（frontmatter + 文档）
├── scripts/                         ← 实现（Python / Shell / Node）
├── README.md                        ← 单技能安装与使用说明
└── examples/ · references/          ← 可选资源

```

**`paid` 字段**放在 `skills.yaml`（本仓库）中，而不是每个 SKILL.md 里——它是商业分类，不是技能本身的属性。付费技能代码私有，但公开的触发信息（名称、简介、分类）仍在此索引，以便 agentskills.io 展示并引导购买。

## 贡献

- **新增技能**：用 [`skill-creator`](https://github.com/lovstudio/skill-creator-skill) 脚手架生成。Skill 可以直接放入本仓库的 `skills/<name>/`，也可以创建 `lovstudio/{name}-skill` 独立仓库；然后在本仓库的 `skills.yaml` 登记。
- **现有技能**：请在技能自己的仓库中提 issue / PR。
- **索引修正**（分类、描述、链接）：向本仓库的 `skills.yaml` 提 PR。**不要改动 README 表格**——CI 会自动重新生成。

## 许可证

- **本索引仓库**：MIT
- **免费技能**：MIT（详见各仓库的 LICENSE）
- **付费技能**：商业许可——详见各技能的购买页面

## Star 历史

[![Star History Chart](https://api.star-history.com/svg?repos=lovstudio/skills&type=Date)](https://star-history.com/#lovstudio/skills&Date)

---

<p align="center">
  <sub>使用 <a href="https://claude.com/claude-code">Claude Code</a> 构建 · 由 <a href="https://lovstudio.ai">Lovstudio</a> 出品</sub>
</p>
