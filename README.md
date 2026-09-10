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
> **163 个技能** — 147 个免费 + 16 个付费。
<!-- COUNT:END -->

<!-- SKILLS:START -->
| | 英文名 | 中文名 | 描述 |
|---|---|---|---|
| **通用** | | | |
| ![Free](https://img.shields.io/badge/Free-green) | [Requirements Compass](https://github.com/lovstudio/skills) (`brainstorm`) | [需求梳理](https://github.com/lovstudio/skills) | 通过证据和聚焦追问明确需求、约束、取舍及验收条件 — 依赖: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Website Filing Assistant](https://github.com/lovstudio/china-website-filing-skill) (`china-website-filing`) | [网站备案助手](https://github.com/lovstudio/china-website-filing-skill) | 把中国大陆网站从备案准备推进到 ICP、域名上线、公安联网备案与合规巡检，并保留权威证据链。 |
| ![Paid](https://img.shields.io/badge/Paid-blueviolet) | [Mac Cleaner](https://github.com/lovstudio/macos-disk-optimizer-skill) (`clean-mac`) | [Mac 清理助手](https://github.com/lovstudio/macos-disk-optimizer-skill) | 按目标容量整理 Mac 磁盘，保护 Screen Studio 等应用工作区，并以可回滚操作和真实可用空间完成验收。 |
| ![Free](https://img.shields.io/badge/Free-green) | [QR Studio](https://github.com/lovstudio/create-qrcode-skill) (`create-qrcode`) | [二维码工坊](https://github.com/lovstudio/create-qrcode-skill) | 复用已保存偏好生成可扫码二维码；默认只输出码本体，明确需要时才加海报框架。 — 依赖: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Dev Diary](https://github.com/lovstudio/skills) (`daily-post`) | [开发日记](https://github.com/lovstudio/skills) | 将近期真实项目更新写成面向读者的简短日更文案 — 依赖: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Image Narrator](https://github.com/lovstudio/describe-image-skill) (`describe-image`) | [看图说话](https://github.com/lovstudio/describe-image-skill) | 给纯文本模型"看图"：用免费视觉模型把任意图片转成文字描述。 |
| ![Free](https://img.shields.io/badge/Free-green) | [Fact Checker](https://github.com/lovstudio/fact-check-skill) (`fact-check`) | [事实核查员](https://github.com/lovstudio/fact-check-skill) | 用尽调思路确认事实：查一手资料、找反例、标证据等级，给出置信度和下一步。 — 相关: `image-translation-errata` |
| ![Free](https://img.shields.io/badge/Free-green) | [Five-Unit Replies](https://github.com/lovstudio/skills) (`five`) | [五字答](https://github.com/lovstudio/skills) | 在明确要求时使用五单位以内的简短回复，并支持随时恢复正常 — 依赖: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Hanzi Lens](https://github.com/lovstudio/hanzi-lens-skill) (`hanzi-lens`) | [汉字镜](https://github.com/lovstudio/hanzi-lens-skill) | 用证据看懂一个汉字：读音、字形、字书、经典语境与专业信息图。 — 依赖: `professional-infographic` |
| ![Free](https://img.shields.io/badge/Free-green) | [Image Maker](https://github.com/lovstudio/image-creator-skill) (`image-creator`) | [造图师](https://github.com/lovstudio/image-creator-skill) | 按用途生成图像、制作可编辑图文布局或整理图像提示词 — 依赖: `branding-consistency`; 相关: `professional-infographic`, `professional-portrait`, `riso-portrait`, `image-translation-errata` |
| ![Free](https://img.shields.io/badge/Free-green) | [Image Translation Review](https://github.com/lovstudio/image-translation-errata-skill) (`image-translation-errata`) | [图片译校](https://github.com/lovstudio/image-translation-errata-skill) | 保留错误机翻的证据，用校样式删改给出正确译文，同时尽量不动原图布局。 — 相关: `translation-review`, `image-creator`, `fact-check` |
| ![Free](https://img.shields.io/badge/Free-green) | [Knowledge Organizer](https://github.com/lovstudio/skills) (`kb-organize`) | [知识库管家](https://github.com/lovstudio/skills) | 检查并整理知识库索引、重复文档、图片位置和内部引用 — 依赖: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Media Downloader](https://github.com/lovstudio/media-crawler-skill) (`media-crawler`) | [媒体下载器](https://github.com/lovstudio/media-crawler-skill) | 将有权保存的视频号等社交媒体链接变成可验证的本地媒体文件与诊断报告。 |
| ![Free](https://img.shields.io/badge/Free-green) | [Media Finder](https://github.com/lovstudio/media-fetch-skill) (`media-fetch`) | [影视寻宝](https://github.com/lovstudio/media-fetch-skill) | 检索并选择合适版本，qBittorrent 与 aria2 续传兜底，最后验收本地媒体与字幕状态。 |
| ![Free](https://img.shields.io/badge/Free-green) | [Knowledge Capture](https://github.com/lovstudio/skills) (`memory-add`) | [知识入库](https://github.com/lovstudio/skills) | 将用户指定信息保存为带分类、标签和来源的知识文档及索引 — 依赖: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Knowledge Finder](https://github.com/lovstudio/skills) (`memory-search`) | [知识寻回](https://github.com/lovstudio/skills) | 跨已配置的 memory 与 distill 知识记录检索并返回可追溯结果 — 依赖: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Image Prompt Crafter](https://github.com/lovstudio/skills) (`nano-banana-pro`) | [图像提示师](https://github.com/lovstudio/skills) | 将图像需求整理为结构清晰、遵循参考素材的生成或编辑提示词 — 依赖: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Content Keeper](https://github.com/lovstudio/skills) (`output`) | [内容收纳](https://github.com/lovstudio/skills) | 将已确认内容按指定文件名与文本格式保存并回读校验 — 依赖: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [WeChat Moments Copy](https://github.com/lovstudio/skills) (`output-wechat-moment`) | [朋友圈文案](https://github.com/lovstudio/skills) | 把已有内容整理成适合朋友圈阅读的纯文本并保存文件 — 依赖: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [My Vocabulary](https://github.com/lovstudio/personal-vocabulary-skill) (`personal-vocabulary`) | [我的词库](https://github.com/lovstudio/personal-vocabulary-skill) | 一份可跨语音输入法复用的个人词汇表。 |
| ![Free](https://img.shields.io/badge/Free-green) | [A Little Encouragement](https://github.com/lovstudio/praise-before-work-skill) (`praise-before-work`) | [开工夸夸](https://github.com/lovstudio/praise-before-work-skill) | 开工前先收到一段具体的夸奖，再开始处理任务。 |
| ![Free](https://img.shields.io/badge/Free-green) | [WeChat Article Reader](https://github.com/MarkShawn2020/read-wechat-article-skill) (`read-wechat-article`) | [公众号文章读取器](https://github.com/MarkShawn2020/read-wechat-article-skill) | 把公开公众号文章整理为可离线 Markdown，保留正文、原图和来源。 — 依赖: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [File Finder](https://github.com/lovstudio/search-file-skill) (`search-file`) | [文件寻踪](https://github.com/lovstudio/search-file-skill) | 从历史 AI 对话找回仍然存在的文件，并用会话证据与存储耐久度排序。 |
| ![Free](https://img.shields.io/badge/Free-green) | [X Post Recovery](https://github.com/lovstudio/search-twitter-skill) (`search-twitter`) | [X 原帖寻回](https://github.com/lovstudio/search-twitter-skill) | 恢复 X/Twitter 逐字正文与截图证据，并明确列出仍无法证明的缺口。 |
| ![Paid](https://img.shields.io/badge/Paid-blueviolet) | [Subtitle Freedom](https://github.com/lovstudio/subtitle-freedom-skill) (`subtitle-freedom`) | [人人字幕](https://github.com/lovstudio/subtitle-freedom-skill) | 以用户选定级别为最低难度线生成英语学习字幕，覆盖更高难度表达，并可选生成不剧透人物卡片与不烧录视频的 ASS/PGS 水印外置字幕。 |
| ![Free](https://img.shields.io/badge/Free-green) | [Deep Thinking](https://github.com/lovstudio/skills) (`think`) | [深度思考](https://github.com/lovstudio/skills) | 围绕复杂问题比较方案、验证假设并给出有依据的决策建议 — 依赖: `branding-consistency` |
| ![Paid](https://img.shields.io/badge/Paid-blueviolet) | [Dictation Editor](https://github.com/lovstudio/typeless-prompt-skill) (`typeless-prompt`) | [口述成文](https://github.com/lovstudio/typeless-prompt-skill) | 消解口癖、重复和改口，把口述草稿整理成逻辑清楚、排版舒展、可直接发送的正文。 |
| ![Paid](https://img.shields.io/badge/Paid-blueviolet) | [Universal WeChat Key](https://github.com/lovstudio/wdb-cli-skill) (`wdb-cli`) | [万能微信秘钥](https://github.com/lovstudio/wdb-cli-skill) | 先为本机微信准备密钥，再通过隔离副本读取数据并保留精确记录身份。 — 依赖: `branding-consistency` |
| ![Paid](https://img.shields.io/badge/Paid-blueviolet) | [Weitan CLI](https://github.com/lovstudio/wxmp-cli-skill) (`wxmp-cli`) | [微探命令行](https://github.com/lovstudio/wxmp-cli-skill) | 检索公众号文章缓存，导出四种格式，内含完整命令行运行包 — 依赖: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Xiaohongshu Researcher](https://github.com/lovstudio/xhs-skill) (`xhs`) | [小红书调研助手](https://github.com/lovstudio/xhs-skill) | 把小红书主题变成有来源的调研报告，而不只是再搜一次。 — 依赖: `branding-consistency` |
| **商务** | | | |
| ![Free](https://img.shields.io/badge/Free-green) | [BP Studio](https://github.com/lovstudio/bp-skill) (`bp`) | [BP 工坊](https://github.com/lovstudio/bp-skill) | 可组合的投资人 BP 工具包：大纲、PPT 制作、审稿润色既能单独使用，也能串成完整流程。 — 依赖: `bp-outline`, `bp-deck`, `bp-polish` |
| ![Free](https://img.shields.io/badge/Free-green) | [BP Master](https://github.com/lovstudio/bp-skill) (`bp-deck`) | [BP 大师](https://github.com/lovstudio/bp-skill) | 把已经确认的 BP 大纲做成风格统一、图表专业的 PPTX、PDF 和全稿预览。 — 依赖: `any2deck` |
| ![Free](https://img.shields.io/badge/Free-green) | [BP Blueprint](https://github.com/lovstudio/bp-skill) (`bp-outline`) | [BP 蓝图](https://github.com/lovstudio/bp-skill) | 先把项目材料变成证据账本和投资人看得懂的 12–15 页大纲，再决定是否制作 PPT。 |
| ![Free](https://img.shields.io/badge/Free-green) | [BP Polish](https://github.com/lovstudio/bp-skill) (`bp-polish`) | [BP 精修](https://github.com/lovstudio/bp-skill) | 给已有 BP 做投资逻辑、证据、文字、图表和视觉体检，输出评分报告与逐页修改，不为好看改事实。 |
| ![Free](https://img.shields.io/badge/Free-green) | [Contract Reviewer](https://github.com/lovstudio/contract-review-pro-skill) (`contract-review-pro`) | [合同批注专家](https://github.com/lovstudio/contract-review-pro-skill) | 专业级合同审阅 — 四层方法论（主体核验 + 基础 + 业务 + 法务），结构化批注含风险等级，附合同摘要、综合意见与业务流程图。 |
| ![Paid](https://img.shields.io/badge/Paid-blueviolet) | [Event Planner](https://github.com/lovstudio/event-curator-skill) (`event-curator`) | [活动策划师](https://github.com/lovstudio/event-curator-skill) | 从嘉宾履历一键生成可交付的活动策划案 — 主题文案、分钟级 rundown、主持人问题卡、伴手礼。 — 相关: `publish-event-onto-hdx` |
| ![Free](https://img.shields.io/badge/Free-green) | [Expense Assistant](https://github.com/lovstudio/expense-report-skill) (`expense-report`) | [报销管家](https://github.com/lovstudio/expense-report-skill) | 发票图片或文字一键整理成分类报销 Excel，业务招待、差旅、办公自动归类。 |
| ![Paid](https://img.shields.io/badge/Paid-blueviolet) | [Proposal Expert](https://github.com/lovstudio/proposal-skill) (`proposal`) | [提案专家](https://github.com/lovstudio/proposal-skill) | 把项目简述一键变成可交付的商业提案，方案、报价、排版全配齐。 |
| ![Free](https://img.shields.io/badge/Free-green) | [Huodongxing Diagnostics](https://github.com/lovstudio/publish-event-onto-hdx-skill) (`publish-event-onto-hdx`) | [活动行诊断](https://github.com/lovstudio/publish-event-onto-hdx-skill) | 一次看清活动行活动为什么在分类页找不到，以及改哪个字段、用哪种排序能被看见。 — 相关: `event-curator`, `event-poster` |
| ![Free](https://img.shields.io/badge/Free-green) | [Contract Polish](https://github.com/lovstudio/review-doc-skill) (`review-doc`) | [合同精修](https://github.com/lovstudio/review-doc-skill) | 审阅文档或合同，输出带批注的 docx，直接拿给同事或客户。 |
| ![Free](https://img.shields.io/badge/Free-green) | [Solution Architect](https://github.com/lovstudio/solution-architect-skill) (`solution-architect`) | [方案架构师](https://github.com/lovstudio/solution-architect-skill) | 把产品或技术需求转成有调研依据、开源优先的可执行解决方案。 |
| **设计** | | | |
| ![Free](https://img.shields.io/badge/Free-green) | [Business Card Studio](https://github.com/lovstudio/business-card-skill) (`business-card`) | [名片工坊](https://github.com/lovstudio/business-card-skill) | 把任何人的姓名、头衔、金句一键变成精美的编辑式名片，输出高清 PNG 与可点击下载的 HTML。 |
| ![Paid](https://img.shields.io/badge/Paid-blueviolet) | [Professional Poster](https://github.com/lovstudio/event-poster-skill) (`event-poster`) | [专业海报](https://github.com/lovstudio/event-poster-skill) | 把活动信息一键变成高质感海报，可直接分享或用于线下展览。 — 相关: `publish-event-onto-hdx` |
| ![Free](https://img.shields.io/badge/Free-green) | [Logo Radar](https://github.com/lovstudio/find-logo-skill) (`find-logo`) | [Logo 雷达](https://github.com/lovstudio/find-logo-skill) | 按品牌名或网址抓取 logo，自动评分择优（偏好长条形 + 透明底），统一归档到本地，方便网站/PPT/海报罗列。 |
| ![Free](https://img.shields.io/badge/Free-green) | [Interface Designer](https://github.com/lovstudio/frontend-design-skill) (`frontend-design`) | [界面设计师](https://github.com/lovstudio/frontend-design-skill) | 把真实内容和现有代码落实为有辨识度、交互一致、媒体可用的界面，并留下验收证据。 — 依赖: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Partner Directory](https://github.com/lovstudio/maintain-partners-skill) (`maintain-partners`) | [伙伴名录](https://github.com/lovstudio/maintain-partners-skill) | 一键抓取品牌 logo、标准化处理并接入官网 partners 区块，多语言全覆盖。 — 依赖: `find-logo` |
| ![Paid](https://img.shields.io/badge/Paid-blueviolet) | [Website Whiz](https://github.com/lovstudio/oh-my-landingpage-skill) (`oh-my-landingpage`) | [官网小能手](https://github.com/lovstudio/oh-my-landingpage-skill) | 从产品与品牌事实出发，独立推导适合当前产品的叙事与视觉，并完成实现、响应式和生产回读。 |
| ![Paid](https://img.shields.io/badge/Paid-blueviolet) | [Professional Infographic](https://github.com/lovstudio/professional-infographic-skill) (`professional-infographic`) | [专业信息图](https://github.com/lovstudio/professional-infographic-skill) | 把复杂材料或投资路径重构为一条可回溯的视觉论证，从进入、分阶段退出到最终判断。 — 相关: `image-creator` |
| ![Free](https://img.shields.io/badge/Free-green) | [Professional Portrait](https://github.com/lovstudio/professional-portrait-skill) (`professional-portrait`) | [职业形象照](https://github.com/lovstudio/professional-portrait-skill) | 把一张普通人像修成干净、自然、仍然像本人的职业形象照。 — 相关: `image-creator`, `riso-portrait` |
| ![Free](https://img.shields.io/badge/Free-green) | [Riso Portrait](https://github.com/lovstudio/riso-portrait-skill) (`riso-portrait`) | [Riso 人像](https://github.com/lovstudio/riso-portrait-skill) | 把一张照片重绘成仍然像本人的 Riso 头像，并检查五官、手指、物件与圆形裁切。 — 相关: `image-creator`, `professional-portrait` |
| ![Paid](https://img.shields.io/badge/Paid-blueviolet) | [Style Sampler](https://github.com/lovstudio/visual-clone-skill) (`visual-clone`) | [风格采样](https://github.com/lovstudio/visual-clone-skill) | 从参考图中提取设计要素，生成可复刻同款风格的指令。 |
| **学术** | | | |
| ![Paid](https://img.shields.io/badge/Paid-blueviolet) | [Academic Translator](https://github.com/lovstudio/academic-translator-skill) (`academic-translator`) | [学术译者](https://github.com/lovstudio/academic-translator-skill) | 将英文论文译为中文，优先保留图表、公式、页码对应与目录跳转。 — 售价 70 Credits |
| ![Paid](https://img.shields.io/badge/Paid-blueviolet) | [Paper Translator](https://github.com/lovstudio/paper-translator-skill) (`paper-translator`) | [论文翻译官](https://github.com/lovstudio/paper-translator-skill) | 将英文论文译为中文 PDF，支持同页数、对照页与段落双语，并在保版式路线中保留图表和公式。 — 售价 70 Credits |
| ![Free](https://img.shields.io/badge/Free-green) | [Thesis Polish](https://github.com/lovstudio/thesis-polish-skill) (`thesis-polish`) | [论文精修](https://github.com/lovstudio/thesis-polish-skill) | MBA 论文全维度润色，对标国优标准，打磨语言、结构、论证与创新四个面。 |
| ![Free](https://img.shields.io/badge/Free-green) | [Translation Review](https://github.com/lovstudio/translation-review-skill) (`translation-review`) | [译文校对](https://github.com/lovstudio/translation-review-skill) | 中译英译文审阅，从六个维度逐条对照原文，找出问题并给出改写建议。 — 相关: `image-translation-errata` |
| **办公** | | | |
| ![Free](https://img.shields.io/badge/Free-green) | [PPT Master](https://github.com/lovstudio/any2deck-skill) (`any2deck`) | [PPT 大师](https://github.com/lovstudio/any2deck-skill) | 把任意内容变成带设计感的幻灯片，16 种风格可选，导出 PPTX / PDF。 — 相关: `any2pdf`, `any2docx` |
| ![Free](https://img.shields.io/badge/Free-green) | [Word Master](https://github.com/lovstudio/any2docx-skill) (`any2docx`) | [Word 大师](https://github.com/lovstudio/any2docx-skill) | 把 Markdown 转成排版规范的 Word 文档，可以直接发给甲方。 — 相关: `any2pdf`, `any2deck` |
| ![Free](https://img.shields.io/badge/Free-green) | [PDF Master](https://github.com/lovstudio/any2pdf-skill) (`any2pdf`) | [PDF大师](https://github.com/lovstudio/any2pdf-skill) | 把 Markdown 排成出版级 PDF，支持中英混排、代码与表格；新增宋黑阅读，共 16 套主题。 — 相关: `any2docx`, `any2deck` |
| ![Free](https://img.shields.io/badge/Free-green) | [Form Assistant](https://github.com/lovstudio/fill-form-skill) (`fill-form`) | [表单小助手](https://github.com/lovstudio/fill-form-skill) | 自动填写 Word 表单模板，字段识别 + 中英文排版一气呵成。 |
| ![Free](https://img.shields.io/badge/Free-green) | [Web Form Assistant](https://github.com/lovstudio/fill-web-form-skill) (`fill-web-form`) | [网页填表助手](https://github.com/lovstudio/fill-web-form-skill) | 用你本地的知识库来应答网页表单，一轮检索一轮生成，草稿即交付。 |
| ![Free](https://img.shields.io/badge/Free-green) | [PDF Scroll](https://github.com/lovstudio/pdf2png-skill) (`pdf2png`) | [PDF 长图](https://github.com/lovstudio/pdf2png-skill) | 把 PDF 拼成一张长图 PNG，在 macOS 上快到几乎瞬间出图。 |
| ![Free](https://img.shields.io/badge/Free-green) | [Vector Tracer](https://github.com/lovstudio/png2svg-skill) (`png2svg`) | [矢量描摹](https://github.com/lovstudio/png2svg-skill) | 把 PNG 矢量化为高质量 SVG，自动抠背景、曲线平滑。 |
| ![Free](https://img.shields.io/badge/Free-green) | [Rich Export](https://github.com/lovstudio/rich-export-skill) (`rich-export`) | [富文档导出](https://github.com/lovstudio/rich-export-skill) | 一份富媒体内容，同时交付网页、可编辑文档、打印版和归档包。 |
| ![Free](https://img.shields.io/badge/Free-green) | [Yoda Automation](https://github.com/lovstudio/yoda-automation-skill) (`yoda-automation`) | [Yoda 自动化](https://github.com/lovstudio/yoda-automation-skill) | 把一次性提醒和周期跟进变成可核验的 Yoda 原生自动化，带时区、运行证据、去重与完成后停用。 |
| **内容创作** | | | |
| ![Free](https://img.shields.io/badge/Free-green) | [WeChat Writer](https://github.com/lovstudio/article-creator-skill) (`article-creator`) | [公众号写手](https://github.com/lovstudio/article-creator-skill) | 从材料、旧稿或来源文章生成完整公众号文章包，并完成写作、品牌、双比例视觉、转载保真与质量验收。 — 依赖: `branding-consistency`, `writing-style` |
| ![Free](https://img.shields.io/badge/Free-green) | [Brand Editor](https://github.com/lovstudio/branding-consistency-skill) (`branding-consistency`) | [品牌审校官](https://github.com/lovstudio/branding-consistency-skill) | 从受众、品牌角色、组件惯例和真实发布语境审校可见文案，并允许删除多余文字。 |
| ![Free](https://img.shields.io/badge/Free-green) | [Deep Research](https://github.com/lovstudio/deep-research-skill) (`deep-research`) | [深度研究](https://github.com/lovstudio/deep-research-skill) | 生成带引用、证据和主张校验的深度研究报告，并收集分享 GitHub 等平台的已核验开源方案。 |
| ![Free](https://img.shields.io/badge/Free-green) | [Document Illustrator](https://github.com/lovstudio/document-illustrator-skill) (`document-illustrator`) | [文档插画师](https://github.com/lovstudio/document-illustrator-skill) | 给长文原地配图，先规划插入点再并行出图，最后自动插回原文。 — 依赖: `image-creator` |
| ![Free](https://img.shields.io/badge/Free-green) | [Text Editor](https://github.com/lovstudio/human-writing-skill) (`human-writing`) | [文稿润色师](https://github.com/lovstudio/human-writing-skill) | 先保住作者真实判断，再修篇章结构，最后用 30 项中文指标定位并复测表层问题。 — 依赖: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [WeChat Publisher](https://github.com/lovstudio/publish-wechat-article-skill) (`publish-wechat-article`) | [公众号发布助手](https://github.com/lovstudio/publish-wechat-article-skill) | 统一读取、局部编辑、创建、回读与发布公众号文章，并严格区分草稿、提交发布和正式上线。 — 依赖: `env-management`, `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Voice Replica](https://github.com/lovstudio/style-clone-skill) (`style-clone`) | [文风复刻](https://github.com/lovstudio/style-clone-skill) | 从样本文章中提取文风画像，再把任意内容改写成该文风。 |
| ![Paid](https://img.shields.io/badge/Paid-blueviolet) | [Book Writing Expert](https://github.com/lovstudio/write-professional-book-skill) (`write-professional-book`) | [写书专家](https://github.com/lovstudio/write-professional-book-skill) | 从大纲开始，逐章写出一本完整的书，技术、教程、专著多种风格。 |
| ![Free](https://img.shields.io/badge/Free-green) | [My Writing Voice](https://github.com/lovstudio/writing-style-skill) (`writing-style`) | [我的文风](https://github.com/lovstudio/writing-style-skill) | 用 19 篇真实样本校准的个人声音完成新写、保真改写与诊断，并经过作者性、篇章、表层和品牌语境门禁。 — 依赖: `branding-consistency`, `human-writing` |
| ![Paid](https://img.shields.io/badge/Paid-blueviolet) | [WeChat Archiver](https://github.com/lovstudio/wxmp-cracker-skill) (`wxmp-cracker`) | [公众号神器](https://github.com/lovstudio/wxmp-cracker-skill) | 把微信公众号的文章批量归档成可再利用的整洁文本。 |
| **开发工具** | | | |
| ![Free](https://img.shields.io/badge/Free-green) | [Task Capture](https://github.com/lovstudio/skills) (`add-task`) | [任务随手记](https://github.com/lovstudio/skills) | 在当前任务清单中按优先级和位置追加事项并保留已有状态 — 依赖: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Web Tool Studio](https://github.com/lovstudio/skills) (`add-tool`) | [小工具工坊](https://github.com/lovstudio/skills) | 为现有网站新增可用的在线工具，并接入多语言、工具目录、站点地图和必要的成本提示 — 依赖: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Agent Guide Keeper](https://github.com/lovstudio/skills) (`agent-instructions`) | [Agent 规范管家](https://github.com/lovstudio/skills) | 诊断或完善项目 Agent 指令文件，适配不同宿主并保留真实工程约定 — 依赖: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [App Studio](https://github.com/lovstudio/app-generator-skill) (`app-generator`) | [应用工坊](https://github.com/lovstudio/app-generator-skill) | 按需求生成 Lovstudio 级 web、PWA 或 Tauri App，内置品牌、UI、数据层、部署/发布和开发辅助。 |
| ![Free](https://img.shields.io/badge/Free-green) | [Architecture Atlas](https://github.com/lovstudio/skills) (`architecture-documentation`) | [架构图谱](https://github.com/lovstudio/skills) | 从项目实际实现生成架构视图、接口说明与决策记录草稿 — 依赖: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Ataru Indexing](https://github.com/lovstudio/ataru-indexing-skill) (`ataru-indexing`) | [Ataru 索引](https://github.com/lovstudio/ataru-indexing-skill) | 在检索之前，先确认本机的 AI 会话记忆真的可被搜索。 |
| ![Free](https://img.shields.io/badge/Free-green) | [Context Sentinel](https://github.com/lovstudio/auto-context-skill) (`auto-context`) | [上下文哨兵](https://github.com/lovstudio/auto-context-skill) | 监测 Claude Code 上下文是否被污染，适时提示你 /fork 或 /btw。 |
| ![Free](https://img.shields.io/badge/Free-green) | [CSS Polish](https://github.com/lovstudio/skills) (`better-css`) | [CSS 精修](https://github.com/lovstudio/skills) | 清理冗余 CSS 并在现有 Tailwind 项目中重构样式 — 依赖: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [GitHub Repository Description Optimization](https://github.com/lovstudio/skills) (`better-github-desc`) | [GitHub 仓库简介优化](https://github.com/lovstudio/skills) | 依据 README 更新 GitHub 仓库描述、主题标签及已核实的官网链接 — 依赖: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Project Organizer](https://github.com/lovstudio/skills) (`better-project-structure`) | [项目整理师](https://github.com/lovstudio/skills) | 分析任意语言项目的目录职责并渐进调整文件结构和引用 — 依赖: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [README Polish](https://github.com/lovstudio/skills) (`better-readme`) | [README 精修](https://github.com/lovstudio/skills) | 依据项目代码完善 README、安装说明、使用示例与真实品牌资产 — 依赖: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Next.js SEO Assistant](https://github.com/lovstudio/skills) (`better-seo`) | [Next.js SEO 助手](https://github.com/lovstudio/skills) | 检查 Next.js 页面元数据、索引规则、站点地图与分享展示 — 依赖: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Status Line Studio](https://github.com/lovstudio/skills) (`better-statusline`) | [状态栏工坊](https://github.com/lovstudio/skills) | 配置并备份 Agent 状态栏，支持列出历史版本和恢复 — 依赖: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Session Mover](https://github.com/lovstudio/cc-migrate-session) (`cc-migrate-session`) | [会话搬家](https://github.com/lovstudio/cc-migrate-session) | 项目目录搬家后，让 Claude Code 的历史会话还能正常 `--resume`。 |
| ![Free](https://img.shields.io/badge/Free-green) | [Check Balance](https://github.com/lovstudio/check-balance-skill) (`check-balance`) | [额度体检](https://github.com/lovstudio/check-balance-skill) | 在被限流之前，看清每个 agent 账号还剩多少、什么时候重置。 |
| ![Free](https://img.shields.io/badge/Free-green) | [Project Checkpoint](https://github.com/lovstudio/skills) (`checkpoint`) | [项目存档](https://github.com/lovstudio/skills) | 根据当前 Git 差异和历史记录保存项目里程碑及后续事项 — 依赖: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Checkpoint History](https://github.com/lovstudio/skills) (`checkpoint-list`) | [检查点回看](https://github.com/lovstudio/skills) | 汇总 Git 与项目日志中的检查点、时间范围和演进记录 — 依赖: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Clash Network Doctor](https://github.com/lovstudio/clash-tun-doctor-skill) (`clash-tun-doctor`) | [Clash 网络医生](https://github.com/lovstudio/clash-tun-doctor-skill) | 从最终运行态和日志诊断 Clash TUN 故障，执行可回滚修复并验证真实应用链路。 — 相关: `env-management` |
| ![Free](https://img.shields.io/badge/Free-green) | [API Studio](https://github.com/lovstudio/cli2anything-skill) (`cli2anything`) | [接口工坊](https://github.com/lovstudio/cli2anything-skill) | 把已授权观察到的网站 API 变成可验证的 OpenAPI、SDK、Swagger 与任务型 CLI。 |
| ![Free](https://img.shields.io/badge/Free-green) | [Project Makeover](https://github.com/lovstudio/skills) (`clone-rebrand`) | [项目换装](https://github.com/lovstudio/skills) | 将模板或 fork 改造为新项目，按范围同步品牌、语言和部署设置 — 依赖: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Code Reviewer](https://github.com/lovstudio/skills) (`code-review`) | [代码审阅官](https://github.com/lovstudio/skills) | 审查实际差异中的正确性、安全和维护风险并给出可定位意见 — 依赖: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Vercel Deployer](https://github.com/lovstudio/deploy-to-vercel-skill) (`deploy-to-vercel`) | [Vercel 部署助手](https://github.com/lovstudio/deploy-to-vercel-skill) | 一键把前端部署到 Vercel，自动配好 Cloudflare DNS 和自定义域名。 |
| ![Free](https://img.shields.io/badge/Free-green) | [Tech Selection Advisor](https://github.com/lovstudio/skills) (`dev-research`) | [技术选型顾问](https://github.com/lovstudio/skills) | 根据软件需求比较复用策略并输出有来源的技术选型与研发计划 — 依赖: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Lesson Distiller](https://github.com/lovstudio/skills) (`distill`) | [经验萃取](https://github.com/lovstudio/skills) | 将真实解决过程整理为可复用经验文档并维护知识索引 — 依赖: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Lessons to Rules](https://github.com/lovstudio/skills) (`distill-to-system`) | [经验入规](https://github.com/lovstudio/skills) | 把有证据的可复用经验写入最合适的项目或共享 Agent 规范 — 依赖: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [DSH Plugin Studio](https://github.com/lovstudio/dsh-plugin-creator-skill) (`dsh-plugin-creator`) | [DSH 插件工坊](https://github.com/lovstudio/dsh-plugin-creator-skill) | 端到端开发 DSH 插件：选扩展点、搭脚手架、实现并通过仓库门槛。 — 相关: `dsh-plugin-publisher` |
| ![Free](https://img.shields.io/badge/Free-green) | [DSH Plugin Publisher](https://github.com/lovstudio/dsh-plugin-publisher-skill) (`dsh-plugin-publisher`) | [DSH 插件发布](https://github.com/lovstudio/dsh-plugin-publisher-skill) | 把已验证的 DSH 插件发布到 npm/git/tarball 渠道，并逐一核验可加载。 — 相关: `dsh-plugin-creator` |
| ![Free](https://img.shields.io/badge/Free-green) | [Desktop App Relaunch](https://github.com/lovstudio/electron-app-relaunch-skill) (`electron-app-relaunch`) | [桌面应用重启](https://github.com/lovstudio/electron-app-relaunch-skill) | 为 Electron 实现真正的完整应用重启，并清晰区分界面刷新与更新交接。 |
| ![Free](https://img.shields.io/badge/Free-green) | [Electron Delta Updates](https://github.com/lovstudio/electron-delta-updater-skill) (`electron-delta-updater`) | [Electron 增量更新](https://github.com/lovstudio/electron-delta-updater-skill) | 为 Electron 应用建立可验证的增量自动更新，覆盖 Sparkle、appcast、签名与真实安装验证。 |
| ![Free](https://img.shields.io/badge/Free-green) | [Credential Keeper](https://github.com/lovstudio/env-management-skill) (`env-management`) | [凭据管家](https://github.com/lovstudio/env-management-skill) | 用平台、账号与 Key 账本管理轮换和有效期，为每个环境目标只选择一个生效 Key，并保持 Dashboard 全程脱敏。 — 相关: `install-ai`, `clash-tun-doctor` |
| ![Free](https://img.shields.io/badge/Free-green) | [Finder Actions](https://github.com/lovstudio/finder-action-skill) (`finder-action`) | [Finder 快捷动作](https://github.com/lovstudio/finder-action-skill) | 创建 macOS Finder 文件快捷操作或目录背景菜单扩展 — 依赖: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Link Fixer](https://github.com/lovstudio/skills) (`fix-broken-links`) | [链接修补匠](https://github.com/lovstudio/skills) | 核对项目路由及页面链接，修复失效目标并保留有效导航 — 依赖: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Log Detective](https://github.com/lovstudio/skills) (`fix-by-add-log`) | [日志侦探](https://github.com/lovstudio/skills) | 针对难复现问题增加最少的诊断日志并用实际输出定位根因 — 依赖: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Troubleshooter](https://github.com/lovstudio/skills) (`fix-general`) | [故障诊疗](https://github.com/lovstudio/skills) | 根据报错和复现证据定位根因、实施修复并验证原路径 — 依赖: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Verified Fixes](https://github.com/lovstudio/skills) (`fix-until-no-error`) | [验证修复](https://github.com/lovstudio/skills) | 围绕明确验证命令持续定位和修复失败项直到通过或遇到真实阻塞 — 依赖: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Logo Studio](https://github.com/lovstudio/skills) (`gen-logo`) | [Logo 工坊](https://github.com/lovstudio/skills) | 根据项目用途制作版本化 Logo 草稿及应用图标，并按确认范围接入 — 依赖: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Project Namer](https://github.com/lovstudio/skills) (`gen-project-name`) | [项目起名师](https://github.com/lovstudio/skills) | 根据项目用途提供可用于文件夹与仓库的名称及定位说明 — 依赖: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [GitHub Collaborator Manager](https://github.com/lovstudio/gh-access-skill) (`gh-access`) | [GitHub 协作管家](https://github.com/lovstudio/gh-access-skill) | 一条命令给私有 GitHub 仓库加减协作者权限，或盘点现有访问清单。 |
| ![Free](https://img.shields.io/badge/Free-green) | [Open Source Contributor](https://github.com/lovstudio/gh-contribute-skill) (`gh-contribute`) | [开源贡献助手](https://github.com/lovstudio/gh-contribute-skill) | 给任意上游 GitHub 仓库提一份干净的 PR——fork、分支、推送、开 PR 一站搞定。 |
| ![Free](https://img.shields.io/badge/Free-green) | [GitHub Organizer](https://github.com/lovstudio/gh-tidy-skill) (`gh-tidy`) | [GitHub 整理师](https://github.com/lovstudio/gh-tidy-skill) | 一次过清理 GitHub 上的 issue、PR、分支和标签，让仓库重新整洁。 |
| ![Free](https://img.shields.io/badge/Free-green) | [Context Commit](https://github.com/lovstudio/skills) (`git-commit-with-context`) | [会话提交](https://github.com/lovstudio/skills) | 结合会话意图与实际 Git 差异生成并执行范围准确的提交 — 依赖: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Command Helper](https://github.com/lovstudio/skills) (`help-cmd`) | [命令助手](https://github.com/lovstudio/skills) | 把操作目标转换为适合当前系统和 shell 的可执行命令说明 — 依赖: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [I18n Inspector](https://github.com/lovstudio/skills) (`i18n-check-i18n`) | [国际化巡检](https://github.com/lovstudio/skills) | 检查并修复用户可见文案硬编码、缺失翻译键及语言配置 — 依赖: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Document Visuals](https://github.com/lovstudio/skills) (`illustrate`) | [图解文档](https://github.com/lovstudio/skills) | 依据文档内容选择真实素材、图表或生成图并校验插入位置 — 依赖: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Supabase Auth Setup](https://github.com/lovstudio/skills) (`init-auth`) | [Supabase 登录接入](https://github.com/lovstudio/skills) | 为 React 应用接入 Supabase 登录、账户恢复及桌面浏览器 OAuth — 依赖: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Port Setup](https://github.com/lovstudio/skills) (`init-port`) | [端口初始化](https://github.com/lovstudio/skills) | 为项目选择稳定开发端口并更新实际框架启动配置 — 依赖: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [AI Integrator](https://github.com/lovstudio/install-ai-skill) (`install-ai`) | [AI 接入助手](https://github.com/lovstudio/install-ai-skill) | 为 App 初始化可上线的 AI 功能，支持 Agent Client、MaaS、模型偏好和配套 UI。 — 相关: `env-management` |
| ![Free](https://img.shields.io/badge/Free-green) | [Design System Setup](https://github.com/lovstudio/skills) (`install-design`) | [设计系统接入](https://github.com/lovstudio/skills) | 将项目品牌设计规范映射到已有前端样式与组件系统 — 依赖: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [shadcn/ui Setup](https://github.com/lovstudio/skills) (`install-shadcn-ui`) | [shadcn/ui 接入](https://github.com/lovstudio/skills) | 安装并按项目品牌配置 shadcn/ui，保留现有主题和组件修改 — 依赖: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [TanStack Query Setup](https://github.com/lovstudio/install-tanstack-query-skill) (`install-tanstack-query`) | [TanStack Query 接入](https://github.com/lovstudio/install-tanstack-query-skill) | 初始化 TanStack Query，并把分散的请求状态收敛到统一 query keys 和 hooks。 |
| ![Free](https://img.shields.io/badge/Free-green) | [Tauri Icon Setup](https://github.com/lovstudio/skills) (`install-tauri-logo`) | [Tauri 图标助手](https://github.com/lovstudio/skills) | 把已确认 Logo 接入 Tauri 包图标和托盘并核验生成资源 — 依赖: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Website Logo Setup](https://github.com/lovstudio/skills) (`install-web-logo`) | [网站 Logo 助手](https://github.com/lovstudio/skills) | 将正式 Logo 接入 favicon、PWA manifest、网页头部和相关组件 — 依赖: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [ZenMux Setup](https://github.com/lovstudio/skills) (`install-zenmux-api`) | [ZenMux 接入](https://github.com/lovstudio/skills) | 为应用接入 ZenMux 服务端代理，隔离密钥并验证请求链路 — 依赖: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Lovinsp Setup](https://github.com/lovstudio/integrate-lovinsp-skill) (`integrate-lovinsp`) | [Lovinsp 接入](https://github.com/lovstudio/integrate-lovinsp-skill) | 为现有前端项目幂等接入 Lovinsp（含无框架 Vite DOM 标注）并验证点击定位源码能力 — 依赖: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Emoji Makeover](https://github.com/lovstudio/skills) (`kill-emoji`) | [Emoji 换装](https://github.com/lovstudio/skills) | 将界面中不合适的 emoji 替换为语义一致的图标或简洁文案 — 依赖: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Website Legal Pages](https://github.com/lovstudio/skills) (`legal-pages`) | [网站条款助手](https://github.com/lovstudio/skills) | 根据真实业务与数据处理事实生成隐私政策和服务条款页面草稿 — 依赖: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Workflow Studio](https://github.com/lovstudio/skills) (`meta-command`) | [流程工坊](https://github.com/lovstudio/skills) | 把重复操作封装成通用 Skill，并按需提供宿主 slash command 适配入口 — 依赖: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Mobile Fit](https://github.com/lovstudio/mobile-adapt-skill) (`mobile-adapt`) | [移动适配师](https://github.com/lovstudio/mobile-adapt-skill) | 扫描并修复 Web 项目的移动端适配问题——溢出、安全区、视口单位、响应式布局和多级导航。 |
| ![Free](https://img.shields.io/badge/Free-green) | [npm Publisher](https://github.com/lovstudio/lov-npm-publisher-skill) (`npm-publisher`) | [npm 发布助手](https://github.com/lovstudio/lov-npm-publisher-skill) | 自动发布 npm 包，无需重复登录——OIDC trusted publishing 或本地 NPM_TOKEN。 |
| ![Free](https://img.shields.io/badge/Free-green) | [Obsidian Dev Sync](https://github.com/lovstudio/skills) (`obsidian-ensure-dev-sync`) | [Obsidian 开发同步](https://github.com/lovstudio/skills) | 诊断并修复插件构建、Vault 同步及热重载链路 — 依赖: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Obsidian Cache Reset](https://github.com/lovstudio/obsidian-reset-cache-skill) (`obsidian-reset-cache`) | [Obsidian 缓存清理](https://github.com/lovstudio/obsidian-reset-cache-skill) | Obsidian 卡在 Loading cache 时，一键重置缓存救场。 |
| ![Free](https://img.shields.io/badge/Free-green) | [Codex Task Launcher](https://github.com/lovstudio/open-codex-session-skill) (`open-codex-session`) | [Codex 任务直达](https://github.com/lovstudio/open-codex-session-skill) | 给出 thread ID 或刚确认的 session，让 Codex 直接打开准确任务。 |
| ![Free](https://img.shields.io/badge/Free-green) | [Tauri Backend Tuner](https://github.com/lovstudio/optimize-tauri-backend-skill) (`optimize-tauri-backend`) | [Tauri 后端调优](https://github.com/lovstudio/optimize-tauri-backend-skill) | 优化 Tauri 后端结构、命令边界和长 IPC 生命周期，降低 Rust 重启带来的开发摩擦。 |
| ![Free](https://img.shields.io/badge/Free-green) | [Storage Organizer](https://github.com/lovstudio/organize-storage-skill) (`organize-storage`) | [存储整理师](https://github.com/lovstudio/organize-storage-skill) | 把混乱的存储盘整理成项目优先的归档结构，同卷安全迁移、可回滚、不删除。 — 依赖: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Port Keeper](https://github.com/lovstudio/project-port-skill) (`project-port`) | [端口管家](https://github.com/lovstudio/project-port-skill) | 给每个项目分配一个稳定且唯一的开发端口，彻底告别端口撞车。 |
| ![Free](https://img.shields.io/badge/Free-green) | [API Refiner](https://github.com/lovstudio/skills) (`refactor-api`) | [API 精修](https://github.com/lovstudio/skills) | 识别后端接口重复并在保持调用契约的前提下实施重构 — 依赖: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Module Refactorer](https://github.com/lovstudio/skills) (`refactor-modular`) | [模块拆分师](https://github.com/lovstudio/skills) | 按职责拆分长文件并保持公共接口、依赖和行为一致 — 依赖: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Release Pilot](https://github.com/lovstudio/release-via-cicd-skill) (`release-via-cicd`) | [自动发版](https://github.com/lovstudio/release-via-cicd-skill) | 配置或运行现有项目发布流水线，并回读产物与真实上线状态 — 依赖: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Project Renamer](https://github.com/lovstudio/skills) (`rename-project`) | [项目改名](https://github.com/lovstudio/skills) | 在保留兼容键与运行连续性的前提下重命名项目、路径和仓库 — 依赖: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Repository Takeover](https://github.com/lovstudio/skills) (`repo-takeover`) | [仓库接手](https://github.com/lovstudio/skills) | 将已有 clone 连接到用户自己的 GitHub 仓库并保留来源与历史 — 依赖: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Docs Site Builder](https://github.com/lovstudio/repo2docs-skill) (`repo2docs`) | [文档站工坊](https://github.com/lovstudio/repo2docs-skill) | 把任意文件夹（代码、文章、图片）增量编纂成精美的 Fumadocs 文档站，并部署到 {id}.lovstudio.ai/docs。 |
| ![Free](https://img.shields.io/badge/Free-green) | [Chat Finder](https://github.com/lovstudio/search-chat-skill) (`search-chat`) | [会话寻踪](https://github.com/lovstudio/search-chat-skill) | 把你和 AI 已经想清楚的事找回来，并读回它原本的上下文。 |
| ![Free](https://img.shields.io/badge/Free-green) | [Skill Alchemist](https://github.com/lovstudio/skill-distiller-skill) (`skill-distiller`) | [Skill 炼金师](https://github.com/lovstudio/skill-distiller-skill) | 将项目经验蒸馏为边界清晰、可创建且可验收的 Skill 蓝图。 |
| ![Free](https://img.shields.io/badge/Free-green) | [Skill Pricer](https://github.com/lovstudio/skill-pricing-skill) (`skill-pricing`) | [Skill 定价师](https://github.com/lovstudio/skill-pricing-skill) | 从成本、价值、信心度与渠道适配出发，生成可解释的 Skill Pricing Card。 |
| ![Free](https://img.shields.io/badge/Free-green) | [Skill Publisher](https://github.com/lovstudio/skill-publisher-skill) (`skill-publisher`) | [Skill 发布助手](https://github.com/lovstudio/skill-publisher-skill) | 每次发布先自动定价，默认上架 LovStudio 官网，仅在明确要求时扩展到其他渠道。 — 依赖: `skill-pricing` |
| ![Free](https://img.shields.io/badge/Free-green) | [Synology Sync](https://github.com/lovstudio/sync-with-synology-skill) (`sync-with-synology`) | [群晖同步助手](https://github.com/lovstudio/sync-with-synology-skill) | 把本地文件安全迁移到群晖：先校验，再清理本地副本。 |
| ![Free](https://img.shields.io/badge/Free-green) | [Version Keeper](https://github.com/lovstudio/skills) (`version-management`) | [版本管家](https://github.com/lovstudio/skills) | 根据实际包变更生成 changeset，并按请求更新版本与 CHANGELOG — 依赖: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Version Review](https://github.com/lovstudio/skills) (`version-management-manual`) | [版本审阅](https://github.com/lovstudio/skills) | 生成 changeset 草稿并提供编辑入口，审阅后验证版本计划 — 依赖: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [XBTI Gallery](https://github.com/lovstudio/xbti-gallery-skill) (`xbti-gallery`) | [XBTI 图鉴](https://github.com/lovstudio/xbti-gallery-skill) | 从已核实的社区地址或仓库列出可访问的 XBTI 人格测试案例 — 依赖: `branding-consistency` |
| **Video Creation** | | | |
| ![Paid](https://img.shields.io/badge/Paid-blueviolet) | [Video Studio](https://github.com/lovstudio/media-creator-skill) (`media-creator`) | [天才剪辑师](https://github.com/lovstudio/media-creator-skill) | 把录屏和 Screen Studio 源工程整理为可审校视频，以批准字幕生成横竖版成片、封面和质检报告。 — 依赖: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Video Prep](https://github.com/lovstudio/media-preprocessor-skill) (`media-preprocessor`) | [视频素材精整](https://github.com/lovstudio/media-preprocessor-skill) | 把长实录提亮、按内容整理，交付可剪素材与源时间码。 — 依赖: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Video Publisher](https://github.com/lovstudio/media-publisher-skill) (`media-publisher`) | [视频分发助手](https://github.com/lovstudio/media-publisher-skill) | 发布视频号或 B 站时冻结用户终稿，逐项核验封面与字段，经确认后再提交并回读状态。 — 依赖: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Camera Media Keeper](https://github.com/lovstudio/migrate-camera-media-skill) (`migrate-camera-media`) | [相机素材管家](https://github.com/lovstudio/migrate-camera-media-skill) | 把相机素材完整转存到 SSD，逐文件校验，并留下可复查的转存报告。 — 依赖: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [WeChat Channels Publisher](https://github.com/lovstudio/publish-wechat-channels-skill) (`publish-wechat-channels`) | [视频号发布助手](https://github.com/lovstudio/publish-wechat-channels-skill) | 通过视频号助手发布视频，逐项回读文案、话题、封面与原创状态，并核验最终结果。 |
| ![Free](https://img.shields.io/badge/Free-green) | [Video Chapters](https://github.com/lovstudio/video-chapter-skill) (`video-chapter`) | [视频章节师](https://github.com/lovstudio/video-chapter-skill) | 从字幕确定章节，在 React 工作台调整切点与样式，再导出透明章节条、烧录成片或剪辑软件素材包。 |
| ![Free](https://img.shields.io/badge/Free-green) | [Video Stills](https://github.com/lovstudio/video-moments-skill) (`video-moments`) | [精彩定格](https://github.com/lovstudio/video-moments-skill) | 从课程和活动视频挑选真实瞬间，完成色彩还原与统一提亮，交付可回溯的照片组。 — 依赖: `branding-consistency` |
| **Meta** | | | |
| ![Free](https://img.shields.io/badge/Free-green) | [Skill Showcase](https://github.com/lovstudio/skill-add-case-skill) (`skill-add-case`) | [Skill 案例馆](https://github.com/lovstudio/skill-add-case-skill) | 登录即可把满意的 Skill 结果分享成案例，支持手动导入或 Agent 投稿。 — 依赖: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Skill Studio](https://github.com/lovstudio/skill-creator-skill) (`skill-creator`) | [Skill 工坊](https://github.com/lovstudio/skill-creator-skill) | 创建、迁移、验证并安装通用 Skill 与自包含 Skill Kit — 依赖: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Skill Refiner](https://github.com/lovstudio/skill-optimizer-skill) (`skill-optimizer`) | [Skill 精修师](https://github.com/lovstudio/skill-optimizer-skill) | 一键体检并修复现有技能，自动升版本号并追加 CHANGELOG。 |
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
