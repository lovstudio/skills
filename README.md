<p align="center">
  <img src="docs/images/cover.png" alt="lovstudio/skills Cover" width="100%">
</p>

<h1 align="center">lovstudio/skills</h1>

<p align="center">
  <strong>Agent skills for AI coding assistants — document conversion, form filling, and more.</strong><br>
  <strong>AI 编程助手的技能包 — 文档转换、表单填充、图片生成等。</strong><br>
  <sub>Works with Claude Code, Cursor, Copilot, Gemini CLI, and more.</sub>
</p>

<p align="center">
  <!-- BADGES:BEGIN -->
  <img src="https://img.shields.io/badge/skills-23-CC785C?style=flat-square" alt="23 skills">
  <img src="https://img.shields.io/badge/categories-8-181818?style=flat-square" alt="8 categories">
  <!-- BADGES:END -->
  <img src="https://img.shields.io/badge/license-MIT-blue?style=flat-square" alt="MIT License">
</p>

<p align="center">
  <a href="#why--为什么">Why</a> &bull;
  <a href="#skills--技能列表">Skills</a> &bull;
  <a href="#install--安装">Install</a> &bull;
  <a href="#how-it-works--工作原理">How It Works</a> &bull;
  <a href="#pro-skills--专业版">Pro</a> &bull;
  <a href="#license--许可证">License</a>
</p>

---

## Why / 为什么

Claude Code is powerful out of the box &mdash; but generic. It doesn't know *your* workflow, *your* output standards, or *your* domain conventions.

Claude Code 开箱即用很强大 &mdash; 但太通用了。它不了解*你的*工作流、*你的*输出标准、*你的*领域惯例。

**lovstudio/skills** gives Claude Code deep expertise in specific domains, so it delivers professional-grade output on the first try &mdash; not the fifth.

**lovstudio/skills** 赋予 Claude Code 特定领域的深度专业能力，让它第一次就能交付专业级输出 &mdash; 而不是第五次。

> Think of it as hiring a specialist instead of a generalist.
>
> 把它想成雇了一个专家，而不是一个通才。

## Install / 安装

```bash
npx skills add lovstudio/skills
```

You'll be prompted to pick which skills to install. Or install a specific one:

你会被提示选择要安装的技能。也可以直接安装某个：

```bash
npx skills add lovstudio/skills --skill lovstudio:any2pdf
```

## Skills / 技能列表

**23 free skills** across 8 categories. / 8 大类共 **23 个免费技能**。

> ![Free](https://img.shields.io/badge/Free-green) = Open source &nbsp;&nbsp; ![Pro](https://img.shields.io/badge/Pro-blueviolet) = [Pro-exclusive / 专业版独占](#pro-skills--专业版)

<!-- SKILLS:BEGIN -->

### Format & Conversion / 格式转换

| | Skill | Description / 描述 |
|---|-------|-------------------|
| ![Free](https://img.shields.io/badge/Free-green) | **[`any2deck`](skills/lovstudio-any2deck/)** | Content → slide deck images (PPTX/PDF), 16 visual styles <br> 内容转幻灯片，16 种视觉风格 |
| ![Free](https://img.shields.io/badge/Free-green) | **[`any2docx`](skills/lovstudio-any2docx/)** | Markdown → styled DOCX with CJK support <br> Markdown 转 Word 文档 |
| ![Free](https://img.shields.io/badge/Free-green) | **[`any2pdf`](skills/lovstudio-any2pdf/)** | Markdown → typeset PDF with [14 themes](docs/THEME-GALLERY.md) <br> Markdown 转排版 PDF |
| ![Free](https://img.shields.io/badge/Free-green) | **[`pdf2png`](skills/lovstudio-pdf2png/)** | PDF → single concatenated PNG (macOS, ~20x faster) <br> PDF 转竖排拼接 PNG |
| ![Free](https://img.shields.io/badge/Free-green) | **[`png2svg`](skills/lovstudio-png2svg/)** | PNG → high-quality SVG with background removal <br> PNG 转矢量 SVG |

### Business / 商务

| | Skill | Description / 描述 |
|---|-------|-------------------|
| ![Pro](https://img.shields.io/badge/Pro-blueviolet) | **[`proposal`](https://lovstudio.ai/skills/proposal)** | Business proposal with architecture, budget & PDF <br> 完整商业提案（架构 + 预算 + PDF） |
| ![Free](https://img.shields.io/badge/Free-green) | **[`fill-form`](skills/lovstudio-fill-form/)** | Auto-fill Word form templates (.docx) <br> 自动填充 Word 表单 |
| ![Free](https://img.shields.io/badge/Free-green) | **[`fill-web-form`](skills/lovstudio-fill-web-form/)** | Fill web forms via knowledge base search <br> 通过知识库填充网页表单 |
| ![Free](https://img.shields.io/badge/Free-green) | **[`review-doc`](skills/lovstudio-review-doc/)** | Review & annotate documents / contracts <br> 审阅批注文档 / 合同审查 |

### Academic / 学术

| | Skill | Description / 描述 |
|---|-------|-------------------|
| ![Free](https://img.shields.io/badge/Free-green) | **[`thesis-polish`](skills/lovstudio-thesis-polish/)** | Polish MBA thesis to national-level quality <br> MBA 论文润色至优秀水准 |
| ![Free](https://img.shields.io/badge/Free-green) | **[`translation-review`](skills/lovstudio-translation-review/)** | CN→EN translation review across 6 dimensions <br> 中英翻译审校 |

### Authoring / 创作

| | Skill | Description / 描述 |
|---|-------|-------------------|
| ![Pro](https://img.shields.io/badge/Pro-blueviolet) | **[`write-book`](https://lovstudio.ai/skills/write-book)** | Write multi-chapter books (tech, tutorial, monograph) <br> 逐章写书，突破 LLM 上下文限制 |
| ![Free](https://img.shields.io/badge/Free-green) | **[`document-illustrator`](skills/lovstudio-document-illustrator/)** | AI-generated illustrations for documents <br> 为文档智能插入 AI 配图 |
| ![Free](https://img.shields.io/badge/Free-green) | **[`anti-wechat-ai-check`](skills/lovstudio-anti-wechat-ai-check/)** | Detect AI traces & humanize text <br> 检测 AI 痕迹 + 人性化润色 |

### Image & Design / 图片与设计

| | Skill | Description / 描述 |
|---|-------|-------------------|
| ![Free](https://img.shields.io/badge/Free-green) | **[`image-creator`](skills/lovstudio-image-creator/)** | Multi-mechanism image generation (AI / code / prompt) <br> 多机制生图（AI / 代码渲染 / 提示词） |
| ![Pro](https://img.shields.io/badge/Pro-blueviolet) | **[`event-poster`](https://lovstudio.ai/skills/event-poster)** | Generate event posters via HTML + Playwright <br> 活动海报生成 |
| ![Pro](https://img.shields.io/badge/Pro-blueviolet) | **[`visual-clone`](https://lovstudio.ai/skills/visual-clone)** | Extract design DNA from reference images <br> 提取设计要素生成复刻指令 |

### Automation & DevOps / 自动化与运维

| | Skill | Description / 描述 |
|---|-------|-------------------|
| ![Free](https://img.shields.io/badge/Free-green) | **[`deploy-to-vercel`](skills/lovstudio-deploy-to-vercel/)** | One-command Vercel deploy with custom domain <br> 一键部署 Vercel + DNS |
| ![Free](https://img.shields.io/badge/Free-green) | **[`gh-tidy`](skills/lovstudio-gh-tidy/)** | Triage GitHub issues, PRs, branches & labels <br> GitHub 仓库整理 |
| ![Free](https://img.shields.io/badge/Free-green) | **[`finder-action`](skills/lovstudio-finder-action/)** | Mac Finder right-click quick actions <br> Finder 右键菜单 |
| ![Free](https://img.shields.io/badge/Free-green) | **[`obsidian-reset-cache`](skills/lovstudio-obsidian-reset-cache/)** | Fix Obsidian loading issues <br> 重置 Obsidian 缓存 |
| ![Free](https://img.shields.io/badge/Free-green) | **[`project-port`](skills/lovstudio-project-port/)** | Generate unique dev port from project name <br> 生成唯一开发端口号 |
| ![Free](https://img.shields.io/badge/Free-green) | **[`auto-context`](skills/lovstudio-auto-context/)** | Monitor context length & suggest cleanup <br> 监测上下文长度 |

### Skill Development / 技能开发

| | Skill | Description / 描述 |
|---|-------|-------------------|
| ![Free](https://img.shields.io/badge/Free-green) | **[`skill-creator`](skills/lovstudio-skill-creator/)** | Scaffold new skills with lovstudio conventions <br> 快速创建新 skill |
| ![Free](https://img.shields.io/badge/Free-green) | **[`skill-optimizer`](skills/lovstudio-skill-optimizer/)** | Audit, fix & bump skill version <br> 优化 skill 并更新版本 |

### Community / 社区

| | Skill | Description / 描述 |
|---|-------|-------------------|
| ![Free](https://img.shields.io/badge/Free-green) | **[`xbti-creator`](skills/lovstudio-xbti-creator/)** | Create custom BTI personality test websites <br> 创建 BTI 人格测试网站 |
| ![Free](https://img.shields.io/badge/Free-green) | **[`xbti-gallery`](skills/lovstudio-xbti-gallery/)** | Browse community BTI tests <br> 浏览社区人格测试 |

<!-- SKILLS:END -->

## How It Works / 工作原理

```
You ──→ Claude Code ──→ Skill (prompt program) ──→ Professional output
你        │                    │                      专业输出
           │                    ├── Domain knowledge   领域知识
           │                    ├── Output conventions  输出规范
           │                    ├── Quality guardrails  质量护栏
           │                    └── Tool orchestration  工具编排
           │
           └── Still the same Claude Code you know
               还是你熟悉的 Claude Code
```

Each skill is a self-contained prompt program (`SKILL.md`) that:

每个技能都是一个自包含的提示词程序（`SKILL.md`），它会：

1. **Triggers automatically** when you describe a matching task / **自动触发** &mdash; 当你描述匹配的任务时
2. **Injects domain expertise** &mdash; conventions, best practices, output formats / **注入领域专业知识** &mdash; 惯例、最佳实践、输出格式
3. **Orchestrates tools** &mdash; file I/O, git, CLI tools, structured workflows / **编排工具** &mdash; 文件读写、git、CLI 工具、结构化工作流
4. **Enforces quality** &mdash; consistent output that meets professional standards / **保障质量** &mdash; 输出一致且达到专业标准

---

## Pro Skills / 专业版

> **Unlock Commercial-Grade Skills** &mdash; Pro members get access to powerful skills not available in the open-source collection.
>
> **解锁商业级技能** &mdash; Pro 会员可获得开源版中没有的高级技能。

| Pro Skill | What it does / 功能 |
|-----------|-------------------|
| **[`write-book`](https://lovstudio.ai/skills/write-book)** | Write full-length books — compressed summary strategy breaks through LLM context limits <br> 逐章写书，压缩摘要策略突破 LLM 上下文限制 |
| **[`proposal`](https://lovstudio.ai/skills/proposal)** | Business proposals with architecture diagrams, budget tables & PDF export <br> 完整商业提案：架构图 + 预算表 + PDF 输出 |
| **[`event-poster`](https://lovstudio.ai/skills/event-poster)** | Generate event posters via HTML + Playwright rendering <br> 活动海报生成（HTML + Playwright 渲染） |
| **[`visual-clone`](https://lovstudio.ai/skills/visual-clone)** | Extract design DNA from reference images into reusable prompts <br> 从参考图提取设计要素，生成可复用的复刻指令 |
| *more coming soon… / 更多即将推出* | |

**What's included / 包含内容：** 🔓 Full source code / 完整源码 &nbsp;·&nbsp; 🚀 All future updates / 持续更新 &nbsp;·&nbsp; 💬 Priority support / 优先支持

<p align="center">
<strong>👇 微信扫码购买 Pro Skills / Scan to purchase 👇</strong><br><br>
WeChat: <code>YouShouldSpeakHow</code><br>
<sub>添加微信备注「Skills Pro」即可获取购买链接</sub>
</p>

---

## Related / 相关

**[lovstudio/claude-code-plugin](https://github.com/lovstudio/claude-code-plugin)** — Official Lovstudio plugin for Claude Code with hooks, commands, and auto-trigger support for skills like `auto-context`.

**[lovstudio/claude-code-plugin](https://github.com/lovstudio/claude-code-plugin)** — Lovstudio 官方 Claude Code 插件，支持 hooks、commands 和技能自动触发。

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=lovstudio/skills&type=Date)](https://star-history.com/#lovstudio/skills&Date)

## License / 许可证

MIT &mdash; Made by [lovstudio.ai](https://lovstudio.ai)

Contact / 联系: [mark@lovstudio.ai](mailto:mark@lovstudio.ai) · WeChat: `YouShouldSpeakHow`
