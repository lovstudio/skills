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
  <a href="#扩展索引">扩展索引</a> ·
  <a href="#安装">安装</a> ·
  <a href="#工作原理">工作原理</a> ·
  <a href="#贡献">贡献</a> ·
  <a href="#许可证">许可证</a>
</p>

---

## 这是什么

本仓库是 Lovstudio 技能生态的**总索引**。常规技能集合已拆到
[`lovstudio/general-skills`](https://github.com/lovstudio/general-skills)；开发者工具、
xBTI 等专题技能通过下方“扩展索引”链接到各自的子索引仓库。

为了兼容旧安装入口，本仓库暂时仍保留常规技能的清单与安装镜像；新的常规技能更新应进入
`lovstudio/general-skills`。

本仓库包含：

- [`skills.yaml`](skills.yaml) — 机器可读清单。每个技能包含两类描述：`description` 是给 Agent 看的英文触发文案，由 CI 自动从各自 GitHub 仓库 description 同步；`tagline_en` / `tagline_zh` 是给人看的中英文一句话简介，由维护者手工填写，也就是下方表格里展示的那一列。
- [`README.md`](README.md) / [`README.en.md`](README.en.md) — 由清单自动渲染生成。
- [`skills/`](skills) — 面向安装器的同步镜像。免费技能从各自独立仓库同步而来，付费技能只放可公开分发的加密包或占位内容；真正的源码和历史仍以各自 skill repo 为准。

标记为 ![Free](https://img.shields.io/badge/Free-green) 的技能是开源免费的（MIT 协议）。标记为 ![Paid](https://img.shields.io/badge/Paid-blueviolet) 的技能是商业版——私有仓库，需购买后使用。购买或咨询请扫码关注公众号 **手工川**：

<p align="center">
  <img src="assets/shougongchuan-banner.jpg" alt="关注公众号「手工川」获取付费技能" width="720">
</p>

## 技能列表

<!-- COUNT:START -->
> **26 个技能** — 20 个免费 + 6 个付费。
<!-- COUNT:END -->

<!-- SKILLS:START -->
| | 英文名 | 中文名 | 描述 |
|---|---|---|---|
| **通用** | | | |
| ![Free](https://img.shields.io/badge/Free-green) | [`image-creator`](https://github.com/lovstudio/image-creator-skill) | [图像工坊](https://github.com/lovstudio/image-creator-skill) | 按需选择最合适的出图方式：端到端 AI、代码渲染或提示词精修。 |
| **商务** | | | |
| ![Free](https://img.shields.io/badge/Free-green) | [`contract-review-pro`](https://github.com/lovstudio/contract-review-pro-skill) | [合同审阅 · 专业版](https://github.com/lovstudio/contract-review-pro-skill) | 专业级合同审阅 — 四层方法论（主体核验 + 基础 + 业务 + 法务），结构化批注含风险等级，附合同摘要、综合意见与业务流程图。 |
| ![Paid](https://img.shields.io/badge/Paid-blueviolet) | [`event-curator`](https://github.com/lovstudio/event-curator-skill) | [活动策展](https://github.com/lovstudio/event-curator-skill) | 从嘉宾履历一键生成可交付的活动策划案 — 主题文案、分钟级 rundown、主持人问题卡、伴手礼。 |
| ![Free](https://img.shields.io/badge/Free-green) | [`expense-report`](https://github.com/lovstudio/expense-report-skill) | [报销整理](https://github.com/lovstudio/expense-report-skill) | 发票图片或文字一键整理成分类报销 Excel，业务招待、差旅、办公自动归类。 |
| ![Paid](https://img.shields.io/badge/Paid-blueviolet) | [`proposal`](https://github.com/lovstudio/proposal-skill) | [专业需求评估](https://github.com/lovstudio/proposal-skill) | 把项目简述一键变成可交付的商业提案，方案、报价、排版全配齐。 |
| ![Free](https://img.shields.io/badge/Free-green) | [`review-doc`](https://github.com/lovstudio/review-doc-skill) | [合同审阅 · 日常版](https://github.com/lovstudio/review-doc-skill) | 审阅文档或合同，输出带批注的 docx，直接拿给同事或客户。 |
| ![Free](https://img.shields.io/badge/Free-green) | [`solution-architect`](https://github.com/lovstudio/solution-architect-skill) | [解决方案架构师](https://github.com/lovstudio/solution-architect-skill) | 把产品或技术需求转成有调研依据、开源优先的可执行解决方案。 |
| **设计** | | | |
| ![Paid](https://img.shields.io/badge/Paid-blueviolet) | [`event-poster`](https://github.com/lovstudio/event-poster-skill) | [大师级海报生成](https://github.com/lovstudio/event-poster-skill) | 把活动信息一键变成高质感海报，直接拿去发。 |
| ![Free](https://img.shields.io/badge/Free-green) | [`find-logo`](https://github.com/lovstudio/find-logo-skill) | [Logo 狩猎](https://github.com/lovstudio/find-logo-skill) | 按品牌名或网址抓取 logo，自动评分择优（偏好长条形 + 透明底），统一归档到本地，方便网站/PPT/海报罗列。 |
| ![Free](https://img.shields.io/badge/Free-green) | [`maintain-partners`](https://github.com/lovstudio/maintain-partners-skill) | [合作伙伴维护](https://github.com/lovstudio/maintain-partners-skill) | 一键抓取品牌 logo、标准化处理并接入官网 partners 区块，多语言全覆盖。 |
| ![Paid](https://img.shields.io/badge/Paid-blueviolet) | [`visual-clone`](https://github.com/lovstudio/visual-clone-skill) | [像素级海报复刻](https://github.com/lovstudio/visual-clone-skill) | 从参考图中提取设计要素，生成可复刻同款风格的指令。 |
| **学术** | | | |
| ![Free](https://img.shields.io/badge/Free-green) | [`thesis-polish`](https://github.com/lovstudio/thesis-polish-skill) | [论文润色](https://github.com/lovstudio/thesis-polish-skill) | MBA 论文全维度润色，对标国优标准，打磨语言、结构、论证与创新四个面。 |
| ![Free](https://img.shields.io/badge/Free-green) | [`translation-review`](https://github.com/lovstudio/translation-review-skill) | [译文审阅](https://github.com/lovstudio/translation-review-skill) | 中译英译文审阅，从六个维度逐条对照原文，找出问题并给出改写建议。 |
| **办公** | | | |
| ![Free](https://img.shields.io/badge/Free-green) | [`any2deck`](https://github.com/lovstudio/any2deck-skill) | [万物转幻灯](https://github.com/lovstudio/any2deck-skill) | 把任意内容变成带设计感的幻灯片，16 种风格可选，导出 PPTX / PDF。 — 相关: `any2pdf`, `any2docx` |
| ![Free](https://img.shields.io/badge/Free-green) | [`any2docx`](https://github.com/lovstudio/any2docx-skill) | [万物转 Word](https://github.com/lovstudio/any2docx-skill) | 把 Markdown 转成排版规范的 Word 文档，可以直接发给甲方。 — 相关: `any2pdf`, `any2deck` |
| ![Free](https://img.shields.io/badge/Free-green) | [`any2pdf`](https://github.com/lovstudio/any2pdf-skill) | [万物转 PDF](https://github.com/lovstudio/any2pdf-skill) | 把 Markdown 排成出版级 PDF，中英混排、代码块、表格全支持，内置 14 套主题。 — 相关: `any2docx`, `any2deck` |
| ![Free](https://img.shields.io/badge/Free-green) | [`fill-form`](https://github.com/lovstudio/fill-form-skill) | [表单代笔](https://github.com/lovstudio/fill-form-skill) | 自动填写 Word 表单模板，字段识别 + 中英文排版一气呵成。 |
| ![Free](https://img.shields.io/badge/Free-green) | [`fill-web-form`](https://github.com/lovstudio/fill-web-form-skill) | [网页代笔](https://github.com/lovstudio/fill-web-form-skill) | 用你本地的知识库来应答网页表单，一轮检索一轮生成，草稿即交付。 |
| ![Free](https://img.shields.io/badge/Free-green) | [`pdf2png`](https://github.com/lovstudio/pdf2png-skill) | [PDF 出长图](https://github.com/lovstudio/pdf2png-skill) | 把 PDF 拼成一张长图 PNG，在 macOS 上快到几乎瞬间出图。 |
| ![Free](https://img.shields.io/badge/Free-green) | [`png2svg`](https://github.com/lovstudio/png2svg-skill) | [PNG 矢量化](https://github.com/lovstudio/png2svg-skill) | 把 PNG 矢量化为高质量 SVG，自动抠背景、曲线平滑。 |
| **内容创作** | | | |
| ![Free](https://img.shields.io/badge/Free-green) | [`anti-wechat-ai-check`](https://github.com/lovstudio/anti-wechat-ai-check-skill) | [文章去 AI 味](https://github.com/lovstudio/anti-wechat-ai-check-skill) | 检测文章的 AI 味并做人性化润色，帮助稳过微信 3.27 条款的机器判定。 |
| ![Free](https://img.shields.io/badge/Free-green) | [`deep-research`](https://github.com/lovstudio/deep-research-skill) | [深度研究](https://github.com/lovstudio/deep-research-skill) | 生成带引用追踪、证据留存和主张校验的深度研究报告，并输出 Markdown/HTML/PDF。 |
| ![Free](https://img.shields.io/badge/Free-green) | [`document-illustrator`](https://github.com/lovstudio/document-illustrator-skill) | [文档配图](https://github.com/lovstudio/document-illustrator-skill) | 给长文原地配图，先规划插入点再并行出图，最后自动插回原文。 — 依赖: `image-creator` |
| ![Free](https://img.shields.io/badge/Free-green) | [`style-clone`](https://github.com/lovstudio/style-clone-skill) | [文风克隆](https://github.com/lovstudio/style-clone-skill) | 从样本文章中提取文风画像，再把任意内容改写成该文风。 |
| ![Paid](https://img.shields.io/badge/Paid-blueviolet) | [`write-professional-book`](https://github.com/lovstudio/write-professional-book-skill) | [专业写书](https://github.com/lovstudio/write-professional-book-skill) | 从大纲开始，逐章写出一本完整的书，技术、教程、专著多种风格。 |
| ![Paid](https://img.shields.io/badge/Paid-blueviolet) | [`wxmp-cracker`](https://github.com/lovstudio/wxmp-cracker-skill) | [公众号神器](https://github.com/lovstudio/wxmp-cracker-skill) | 把微信公众号的文章批量归档成可再利用的整洁文本。 |
<!-- SKILLS:END -->

<sub>上表由 [`scripts/render-readme.py`](scripts/render-readme.py) 从 [`skills.yaml`](skills.yaml) 自动生成。请编辑 `skills.yaml`，不要手动改表格。</sub>

## 扩展索引

以下专题技能已独立成子索引仓库，自行管理清单与镜像。它们仍属于 Lovstudio
技能生态，但不会在上方常规技能表里逐项展开。按需安装：

| 子索引 | 内容 | 安装 |
|---|---|---|
| [`lovstudio/general-skills`](https://github.com/lovstudio/general-skills) | 常规 Lovstudio 技能：办公、商务、设计、学术、内容创作等 | `npx lovstudio skills add general-skills -g -y` |
| [`lovstudio/dev-skills`](https://github.com/lovstudio/dev-skills) | 开发者与技能作者工具：Meta（skill-creator / skill-optimizer）+ Dev Tools（GitHub、Vercel、macOS、Claude Code session、TanStack Query 初始化/重构等） | `npx lovstudio skills add dev-skills -g -y` |
| [`lovstudio/xbti-skills`](https://github.com/lovstudio/xbti-skills) | xBTI 人格测试定制与画廊（配合 [xbti.lovstudio.ai](https://xbti.lovstudio.ai)） | `npx lovstudio skills add xbti-skills -g -y` |

## 安装

统一使用 `npx lovstudio` 入口，免费付费一致：

```bash
# 装单个技能
npx lovstudio skills add any2pdf -g -y

# 一次安装全部常规技能
npx lovstudio skills add general-skills -g -y

# 付费技能 — 一行带激活
npx lovstudio skills add proposal -k lk-<your-license-key> -g -y

# 单独激活 license（已装过的付费技能也走这条）
npx lovstudio license activate lk-<your-license-key>
```

> `-g` 装到 `~/.claude/skills/`，`-y` 跳过交互确认（AI / CI / 非 TTY 必加）。

通过 [agentskills.io](https://agentskills.io) 可浏览并一键安装。

## 工作原理

```
lovstudio/skills (本仓库)            ← Lovstudio 技能生态总索引
├── README.md                        ← 中文版总索引（默认）
├── README.en.md                     ← English index
└── README / 扩展索引                 ← 指向 general/dev/xBTI 等子索引

lovstudio/general-skills             ← 常规技能索引 + 安装镜像
├── skills.yaml
├── skills/<name>/
└── .claude-plugin/marketplace.json

lovstudio/<name>-skill               ← 常规技能的独立源码仓库
├── SKILL.md                         ← 技能定义（frontmatter + 文档）
├── scripts/                         ← 实现（Python / Shell / Node）
├── README.md                        ← 单技能安装与使用说明
└── examples/ · references/          ← 可选资源

lovstudio/dev-skills                 ← 开发者/技能作者工具子索引
└── skills/<name>/                   ← 聚合分发的 dev/meta skills
```

**`paid` 字段**放在 `skills.yaml`（本仓库）中，而不是每个 SKILL.md 里——它是商业分类，不是技能本身的属性。付费技能代码私有，但公开的触发信息（名称、简介、分类）仍在此索引，以便 agentskills.io 展示并引导购买。

## 贡献

- **新增常规技能**：用 [`skill-creator`](https://github.com/lovstudio/skill-creator-skill) 脚手架生成。然后在 `lovstudio/{name}-skill` 创建仓库，并向 [`lovstudio/general-skills`](https://github.com/lovstudio/general-skills) 提 PR 将其添加到 `skills.yaml`。
- **新增开发者/元技能**：优先放到 [`lovstudio/dev-skills`](https://github.com/lovstudio/dev-skills)，在该子索引内维护 `skills.yaml`、README 和镜像。
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
