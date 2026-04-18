<h1 align="center">Lovstudio Skills</h1>

<p align="center">
  <strong>Lovstudio 所有 Claude Code AI 编程技能的中央索引。</strong><br>
  <sub>由 <a href="https://lovstudio.ai">Lovstudio</a> 出品 · <a href="https://agentskills.io">agentskills.io</a></sub>
</p>

<p align="center">
  <a href="README.md">English</a> · <b>简体中文</b>
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

- [`skills.yaml`](skills.yaml) — 所有技能的机器可读清单（名称、仓库、`paid`、分类、描述）
- [`README.md`](README.md) / [`README.zh-CN.md`](README.zh-CN.md) — 人类可读的技能列表
- 不含代码。技能代码和历史均在各自独立仓库中。

标记为 ![Free](https://img.shields.io/badge/Free-green) 的技能是开源免费的（MIT 协议）。标记为 ![Paid](https://img.shields.io/badge/Paid-blueviolet) 的技能是商业版——私有仓库，需购买后使用。

## 技能列表

<!-- COUNT:START -->
> **32 个技能** — 28 个免费 + 4 个付费。
<!-- COUNT:END -->

<!-- SKILLS:START -->
| | 技能 | 描述 |
|---|---|---|
| **格式转换** | | |
| ![Free](https://img.shields.io/badge/Free-green) | [`any2deck`](https://github.com/lovstudio/any2deck-skill) | Content → slide deck images with 16 visual styles, PPTX/PDF export, branding overlay. |
| ![Free](https://img.shields.io/badge/Free-green) | [`any2docx`](https://github.com/lovstudio/any2docx-skill) | Convert Markdown documents to professionally styled DOCX (Word) files with python-docx. |
| ![Free](https://img.shields.io/badge/Free-green) | [`any2pdf`](https://github.com/lovstudio/any2pdf-skill) | Markdown → professionally typeset PDF. CJK/Latin mixed text, code blocks, tables, 14 themes. |
| ![Free](https://img.shields.io/badge/Free-green) | [`pdf2png`](https://github.com/lovstudio/pdf2png-skill) | PDF → single vertically concatenated PNG. Uses macOS CoreGraphics, ~20x faster than pdftoppm. |
| ![Free](https://img.shields.io/badge/Free-green) | [`png2svg`](https://github.com/lovstudio/png2svg-skill) | PNG → high-quality SVG conversion with background removal and spline curves. |
| **内容处理** | | |
| ![Free](https://img.shields.io/badge/Free-green) | [`anti-wechat-ai-check`](https://github.com/lovstudio/anti-wechat-ai-check-skill) | 检测文章 AI 痕迹 + 人性化润色，通过微信 3.27 条款检测。 |
| ![Free](https://img.shields.io/badge/Free-green) | [`document-illustrator`](https://github.com/lovstudio/document-illustrator-skill) | 为文档原地插入 AI 配图。全局规划插入点，并行生成，异步插回原文。 |
| ![Paid](https://img.shields.io/badge/Paid-blueviolet) | [`write-professional-book`](https://github.com/lovstudio/write-professional-book-skill) | Write multi-chapter books (technical, tutorial, monograph) / 逐章写书，支持多种风格 |
| ![Paid](https://img.shields.io/badge/Paid-blueviolet) | [`wxmp-cracker`](https://github.com/lovstudio/wxmp-cracker-skill) | 微信公众号文章抓取。agent-browser 自动取 token+cookie（首次扫码，之后免扫），失效自动重抿。 |
| **图像与设计** | | |
| ![Paid](https://img.shields.io/badge/Paid-blueviolet) | [`event-poster`](https://github.com/lovstudio/event-poster-skill) | Generate event posters via HTML + Playwright / 活动海报生成 |
| ![Free](https://img.shields.io/badge/Free-green) | [`image-creator`](https://github.com/lovstudio/image-creator-skill) | Multi-mechanism image generation: end-to-end AI, code rendering, or prompt engineering |
| ![Free](https://img.shields.io/badge/Free-green) | [`visual-clone`](https://github.com/lovstudio/visual-clone-skill) | Extract design DNA from reference images / 提取设计要素生成复刻指令 |
| **学术** | | |
| ![Free](https://img.shields.io/badge/Free-green) | [`thesis-polish`](https://github.com/lovstudio/thesis-polish-skill) | MBA 论文全面润色，对标全国优秀论文标准。语言+结构+论证+创新四维提升。 |
| ![Free](https://img.shields.io/badge/Free-green) | [`translation-review`](https://github.com/lovstudio/translation-review-skill) | Chinese-to-English translation review. Compares source & translation across 6 dimensions. |
| **人格测试** | | |
| ![Free](https://img.shields.io/badge/Free-green) | [`xbti-creator`](https://github.com/lovstudio/xbti-creator-skill) | Create custom BTI personality tests (LBTI, FBTI, etc.) with AI-generated content + avatars. |
| ![Free](https://img.shields.io/badge/Free-green) | [`xbti-gallery`](https://github.com/lovstudio/xbti-gallery-skill) | Browse all community-created BTI personality tests at xbti.lovstudio.ai. |
| **财务** | | |
| ![Free](https://img.shields.io/badge/Free-green) | [`expense-report`](https://github.com/lovstudio/expense-report-skill) | 发票图片/文字 → 分类报销 Excel。自动归类：业务招待、差旅、办公用品等。 |
| **办公自动化** | | |
| ![Free](https://img.shields.io/badge/Free-green) | [`fill-form`](https://github.com/lovstudio/fill-form-skill) | Fill Word form templates (.docx). Auto-detects table fields, CJK font support. |
| ![Free](https://img.shields.io/badge/Free-green) | [`fill-web-form`](https://github.com/lovstudio/fill-web-form-skill) | Fill web forms from local knowledge base. Fetch URL → deep-search KB → generate markdown doc. |
| ![Paid](https://img.shields.io/badge/Paid-blueviolet) | [`proposal`](https://github.com/lovstudio/proposal-skill) | Business proposal with architecture, budget & PDF / 完整商业提案 |
| ![Free](https://img.shields.io/badge/Free-green) | [`review-doc`](https://github.com/lovstudio/review-doc-skill) | Review and annotate documents/contracts — output annotated docx with comments |
| **元技能** | | |
| ![Free](https://img.shields.io/badge/Free-green) | [`skill-creator`](https://github.com/lovstudio/skill-creator-skill) | Scaffold new lovstudio skills with proper structure, SKILL.md + README.md. |
| ![Free](https://img.shields.io/badge/Free-green) | [`skill-optimizer`](https://github.com/lovstudio/skill-optimizer-skill) | Audit + auto-fix an existing skill, bump semver, and append a CHANGELOG entry. |
| **开发工具** | | |
| ![Free](https://img.shields.io/badge/Free-green) | [`auto-context`](https://github.com/lovstudio/auto-context-skill) | Context hygiene checker. Suggests /fork or /btw when context is polluted. |
| ![Free](https://img.shields.io/badge/Free-green) | [`cc-migrate-session`](https://github.com/lovstudio/cc-migrate-session) | Migrate Claude Code session history when a project folder moves. Rewrites ~/.claude/projects/<slug>/*.jsonl cwd fields so `claude --resume` keeps working. |
| ![Free](https://img.shields.io/badge/Free-green) | [`deploy-to-vercel`](https://github.com/lovstudio/deploy-to-vercel-skill) | Deploy frontend to Vercel with auto Cloudflare DNS + custom domain setup. |
| ![Free](https://img.shields.io/badge/Free-green) | [`finder-action`](https://github.com/lovstudio/finder-action-skill) | Generate Mac Finder right-click menu actions. Quick Action or Finder Sync Extension. |
| ![Free](https://img.shields.io/badge/Free-green) | [`gh-access`](https://github.com/lovstudio/gh-access-skill) | Grant / revoke / list collaborator access on private GitHub repos by username or email. Read-only by default. |
| ![Free](https://img.shields.io/badge/Free-green) | [`gh-contribute`](https://github.com/lovstudio/gh-contribute-skill) | Contribute clean, professional PRs to upstream GitHub repos — fork, branch, commit, push, open PR, with smart splitting. |
| ![Free](https://img.shields.io/badge/Free-green) | [`gh-tidy`](https://github.com/lovstudio/gh-tidy-skill) | Triage & clean up GitHub issues, PRs, branches, and labels in one pass. |
| ![Free](https://img.shields.io/badge/Free-green) | [`obsidian-reset-cache`](https://github.com/lovstudio/obsidian-reset-cache-skill) | 重置 Obsidian 缓存，解决卡在 Loading cache 的问题。 |
| ![Free](https://img.shields.io/badge/Free-green) | [`project-port`](https://github.com/lovstudio/project-port-skill) | Generate stable unique dev port (3000–8999) from project name. |
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
├── README.md                        ← 英文版索引
├── README.zh-CN.md                  ← 中文版索引
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
