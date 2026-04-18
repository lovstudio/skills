<h1 align="center">Lovstudio Skills</h1>

<p align="center">
  <strong>Lovstudio 所有 Claude Code AI 编程技能的中央索引。</strong><br>
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

本仓库是 Lovstudio 技能的**中央索引**。每个技能都有自己独立的仓库 `github.com/lovstudio/{name}-skill`。本仓库包含：

- [`skills.yaml`](skills.yaml) — 机器可读清单。每个技能包含两类描述：`description` 是给 Agent 看的英文触发文案，由 CI 自动从各自 GitHub 仓库 description 同步；`tagline_en` / `tagline_zh` 是给人看的中英文一句话简介，由维护者手工填写，也就是下方表格里展示的那一列。
- [`README.md`](README.md) / [`README.en.md`](README.en.md) — 由清单自动渲染生成。
- 不含代码。技能代码和历史均在各自独立仓库中。

标记为 ![Free](https://img.shields.io/badge/Free-green) 的技能是开源免费的（MIT 协议）。标记为 ![Paid](https://img.shields.io/badge/Paid-blueviolet) 的技能是商业版——私有仓库，需购买后使用。购买或咨询请扫码关注公众号 **手工川**：

<p align="center">
  <img src="assets/shougongchuan-banner.jpg" alt="关注公众号「手工川」获取付费技能" width="720">
</p>

## 技能列表

<!-- COUNT:START -->
> **32 个技能** — 27 个免费 + 5 个付费。
<!-- COUNT:END -->

<!-- SKILLS:START -->
| | 技能 | 描述 |
|---|---|---|
| **通用** | | |
| ![Free](https://img.shields.io/badge/Free-green) | [图片生成 · `image-creator`](https://github.com/lovstudio/image-creator-skill) | 按需选择最合适的出图方式：端到端 AI、代码渲染或提示词精修。 |
| ![Free](https://img.shields.io/badge/Free-green) | [技能脚手架 · `skill-creator`](https://github.com/lovstudio/skill-creator-skill) | 一条命令生成规范的 Claude Code 技能骨架，结构即对即用。 |
| ![Free](https://img.shields.io/badge/Free-green) | [技能优化器 · `skill-optimizer`](https://github.com/lovstudio/skill-optimizer-skill) | 一键体检并修复现有技能，自动升版本号并追加 CHANGELOG。 |
| **商务** | | |
| ![Paid](https://img.shields.io/badge/Paid-blueviolet) | [商业提案 · `proposal`](https://github.com/lovstudio/proposal-skill) | 把项目简述一键变成可交付的商业提案，方案、报价、排版全配齐。 |
| ![Paid](https://img.shields.io/badge/Paid-blueviolet) | [文档审阅 · `review-doc`](https://github.com/lovstudio/review-doc-skill) | 审阅文档或合同，输出带批注的 docx，直接拿给同事或客户。 |
| **设计** | | |
| ![Paid](https://img.shields.io/badge/Paid-blueviolet) | [活动海报 · `event-poster`](https://github.com/lovstudio/event-poster-skill) | 把活动信息一键变成高质感海报，直接拿去发。 |
| ![Free](https://img.shields.io/badge/Free-green) | [视觉复刻 · `visual-clone`](https://github.com/lovstudio/visual-clone-skill) | 从参考图中提取设计要素，生成可复刻同款风格的指令。 |
| **学术** | | |
| ![Free](https://img.shields.io/badge/Free-green) | [论文润色 · `thesis-polish`](https://github.com/lovstudio/thesis-polish-skill) | MBA 论文全维度润色，对标国优标准，打磨语言、结构、论证与创新四个面。 |
| ![Free](https://img.shields.io/badge/Free-green) | [译文审阅 · `translation-review`](https://github.com/lovstudio/translation-review-skill) | 中译英译文审阅，从六个维度逐条对照原文，找出问题并给出改写建议。 |
| **办公** | | |
| ![Free](https://img.shields.io/badge/Free-green) | [转幻灯片 · `any2deck`](https://github.com/lovstudio/any2deck-skill) | 把任意内容变成带设计感的幻灯片，16 种风格可选，导出 PPTX / PDF。 |
| ![Free](https://img.shields.io/badge/Free-green) | [转 Word · `any2docx`](https://github.com/lovstudio/any2docx-skill) | 把 Markdown 转成排版规范的 Word 文档，可以直接发给甲方。 |
| ![Free](https://img.shields.io/badge/Free-green) | [转 PDF · `any2pdf`](https://github.com/lovstudio/any2pdf-skill) | 把 Markdown 排成出版级 PDF，中英混排、代码块、表格全支持，内置 14 套主题。 |
| ![Free](https://img.shields.io/badge/Free-green) | [Word 表单填写 · `fill-form`](https://github.com/lovstudio/fill-form-skill) | 自动填写 Word 表单模板，字段识别 + 中英文排版一气呵成。 |
| ![Free](https://img.shields.io/badge/Free-green) | [网页表单填写 · `fill-web-form`](https://github.com/lovstudio/fill-web-form-skill) | 用你本地的知识库来应答网页表单，一轮检索一轮生成，草稿即交付。 |
| ![Free](https://img.shields.io/badge/Free-green) | [PDF 转长图 · `pdf2png`](https://github.com/lovstudio/pdf2png-skill) | 把 PDF 拼成一张长图 PNG，在 macOS 上快到几乎瞬间出图。 |
| ![Free](https://img.shields.io/badge/Free-green) | [PNG 转 SVG · `png2svg`](https://github.com/lovstudio/png2svg-skill) | 把 PNG 矢量化为高质量 SVG，自动抠背景、曲线平滑。 |
| **财税** | | |
| ![Free](https://img.shields.io/badge/Free-green) | [报销单整理 · `expense-report`](https://github.com/lovstudio/expense-report-skill) | 发票图片或文字一键整理成分类报销 Excel，业务招待、差旅、办公自动归类。 |
| **内容创作** | | |
| ![Free](https://img.shields.io/badge/Free-green) | [微信 AI 味降检 · `anti-wechat-ai-check`](https://github.com/lovstudio/anti-wechat-ai-check-skill) | 检测文章的 AI 味并做人性化润色，帮助稳过微信 3.27 条款的机器判定。 |
| ![Free](https://img.shields.io/badge/Free-green) | [文档配图 · `document-illustrator`](https://github.com/lovstudio/document-illustrator-skill) | 给长文原地配图，先规划插入点再并行出图，最后自动插回原文。 |
| ![Paid](https://img.shields.io/badge/Paid-blueviolet) | [多章节写书 · `write-professional-book`](https://github.com/lovstudio/write-professional-book-skill) | 从大纲开始，逐章写出一本完整的书，技术、教程、专著多种风格。 |
| ![Paid](https://img.shields.io/badge/Paid-blueviolet) | [公众号抓取 · `wxmp-cracker`](https://github.com/lovstudio/wxmp-cracker-skill) | 把微信公众号的文章批量归档成可再利用的整洁文本。 |
| **开发工具** | | |
| ![Free](https://img.shields.io/badge/Free-green) | [上下文体检 · `auto-context`](https://github.com/lovstudio/auto-context-skill) | 监测 Claude Code 上下文是否被污染，适时提示你 /fork 或 /btw。 |
| ![Free](https://img.shields.io/badge/Free-green) | [会话迁移 · `cc-migrate-session`](https://github.com/lovstudio/cc-migrate-session) | 项目目录搬家后，让 Claude Code 的历史会话还能正常 `--resume`。 |
| ![Free](https://img.shields.io/badge/Free-green) | [部署到 Vercel · `deploy-to-vercel`](https://github.com/lovstudio/deploy-to-vercel-skill) | 一键把前端部署到 Vercel，自动配好 Cloudflare DNS 和自定义域名。 |
| ![Free](https://img.shields.io/badge/Free-green) | [访达右键动作 · `finder-action`](https://github.com/lovstudio/finder-action-skill) | 几分钟给 macOS 访达右键菜单加一个你自己的动作。 |
| ![Free](https://img.shields.io/badge/Free-green) | [GitHub 协作者管理 · `gh-access`](https://github.com/lovstudio/gh-access-skill) | 一条命令给私有 GitHub 仓库加减协作者权限，或盘点现有访问清单。 |
| ![Free](https://img.shields.io/badge/Free-green) | [GitHub 投稿 PR · `gh-contribute`](https://github.com/lovstudio/gh-contribute-skill) | 给任意上游 GitHub 仓库提一份干净的 PR——fork、分支、推送、开 PR 一站搞定。 |
| ![Free](https://img.shields.io/badge/Free-green) | [GitHub 仓库整理 · `gh-tidy`](https://github.com/lovstudio/gh-tidy-skill) | 一次过清理 GitHub 上的 issue、PR、分支和标签，让仓库重新整洁。 |
| ![Free](https://img.shields.io/badge/Free-green) | [重置 Obsidian 缓存 · `obsidian-reset-cache`](https://github.com/lovstudio/obsidian-reset-cache-skill) | Obsidian 卡在 Loading cache 时，一键重置缓存救场。 |
| ![Free](https://img.shields.io/badge/Free-green) | [项目端口分配 · `project-port`](https://github.com/lovstudio/project-port-skill) | 给每个项目分配一个稳定且唯一的开发端口，彻底告别端口撞车。 |
| **人格测试** | | |
| ![Free](https://img.shields.io/badge/Free-green) | [xBTI 测试定制 · `xbti-creator`](https://github.com/lovstudio/xbti-creator-skill) | 定制属于你自己的 BTI 人格测试（LBTI、FBTI 等），题目、结果、头像全自动生成。 |
| ![Free](https://img.shields.io/badge/Free-green) | [xBTI 画廊 · `xbti-gallery`](https://github.com/lovstudio/xbti-gallery-skill) | 浏览社区在 xbti.lovstudio.ai 上发布的所有 BTI 人格测试。 |
<!-- SKILLS:END -->

<sub>上表由 [`scripts/render-readme.py`](scripts/render-readme.py) 从 [`skills.yaml`](skills.yaml) 自动生成。请编辑 `skills.yaml`，不要手动改表格。</sub>

## 安装

每个技能从自己的仓库独立安装，示例：

```bash
# 免费技能
git clone https://github.com/lovstudio/any2pdf-skill ~/.claude/skills/lovstudio-any2pdf

# 付费技能（购买后——使用已授权的 SSH key）
git clone git@github.com:lovstudio/write-professional-book-skill ~/.claude/skills/lovstudio-write-professional-book
```

通过 [agentskills.io](https://agentskills.io) 可浏览并一键安装。

## 工作原理

```
lovstudio/skills (本仓库)            ← 你在这里
├── README.md                        ← 中文版索引（默认）
├── README.en.md                     ← English index
├── skills.yaml                      ← 机器可读清单
└── .github/workflows/               ← CI：渲染 README、同步描述

lovstudio/<name>-skill (27 个仓库)   ← 每个技能的独立仓库
├── SKILL.md                         ← 技能定义（frontmatter + 文档）
├── scripts/                         ← 实现（Python / Shell / Node）
├── README.md                        ← 单技能安装与使用说明
└── examples/ · references/          ← 可选资源
```

**`paid` 字段**放在 `skills.yaml`（本仓库）中，而不是每个 SKILL.md 里——它是商业分类，不是技能本身的属性。付费技能代码私有，但公开的触发信息（名称、简介、分类）仍在此索引，以便 agentskills.io 展示并引导购买。

## 贡献

- **新增技能**：用 [`skill-creator`](https://github.com/lovstudio/skill-creator-skill) 脚手架生成。然后在 `lovstudio/{name}-skill` 创建仓库，并向本仓库提 PR 将其添加到 `skills.yaml`。
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
