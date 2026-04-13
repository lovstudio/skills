<p align="center">
  <img src="docs/images/cover.png" alt="lovstudio/skills Cover" width="100%">
</p>

<h1 align="center">lovstudio/skills</h1>

<p align="center">
  <strong>Agent skills for AI coding assistants — document conversion, form filling, and more</strong><br>
  <sub>Works with Claude Code, Cursor, Copilot, Gemini CLI, and more</sub>
</p>

<p align="center">
  <a href="https://agentskills.io">agentskills.io</a> &middot;
  <a href="https://lovstudio.ai">lovstudio.ai</a> &middot;
  <a href="#install">Install</a> &middot;
  <a href="#available-skills">Skills</a>
</p>

---

## Install

```bash
npx skills add lovstudio/skills
```

You'll be prompted to pick which skills to install. Or install a specific one:

```bash
npx skills add lovstudio/skills --skill lovstudio:any2pdf
```

## Available Skills

### Meta Skills

| Skill | Description |
|-------|-------------|
| [skill-creator](skills/lovstudio-skill-creator/) | Scaffold new lovstudio skills with proper structure, SKILL.md + README.md. |
| [skill-optimizer](skills/lovstudio-skill-optimizer/) | Audit + auto-fix an existing skill, bump semver, and append a CHANGELOG entry. |

### Document Conversion

| Skill | Description |
|-------|-------------|
| [any2pdf](skills/lovstudio-any2pdf/) | Markdown → professionally typeset PDF. CJK/Latin mixed text, code blocks, tables, [14 themes](docs/THEME-GALLERY.md). |
| [any2docx](skills/lovstudio-any2docx/) | Markdown → professionally styled DOCX (Word). Same [14 themes](docs/THEME-GALLERY.md) as any2pdf, editable output. |
| [any2deck](skills/lovstudio-any2deck/) | Content → slide deck images with 16 visual styles, PPTX/PDF export, branding overlay. |
| [png2svg](skills/lovstudio-png2svg/) | PNG → high-quality SVG conversion with background removal and spline curves. |
| [pdf2png](skills/lovstudio-pdf2png/) | PDF → single vertically concatenated PNG. Uses macOS CoreGraphics, ~20x faster than pdftoppm. |
| [md2pdf](skills/lovstudio-md2pdf/) | Markdown → PDF via pandoc + xelatex. CJK support, quick & simple. |

### Content Processing

| Skill | Description |
|-------|-------------|
| [fill-form](skills/lovstudio-fill-form/) | Fill Word form templates (.docx). Auto-detects table fields, CJK font support. |
| [document-illustrator](skills/document-illustrator/) | 为文档原地插入 AI 配图。全局规划插入点，并行生成，异步插回原文。 |
| [translation-review](skills/lovstudio-translation-review/) | Chinese-to-English translation review. Compares source & translation across 6 dimensions, outputs prioritized report. |
| [anti-wechat-ai-check](skills/lovstudio-anti-wechat-ai-check/) | 检测文章 AI 痕迹 + 人性化润色，通过微信 3.27 条款检测。 |
| [thesis-polish](skills/lovstudio-thesis-polish/) | MBA 论文全面润色，对标全国优秀论文标准。语言+结构+论证+创新四维提升。 |

### Content Creation

| Skill | Description |
|-------|-------------|
| [image-creator](skills/lovstudio-image-creator/) | Generate images using Gemini via ZenMux. Supports ASCII art output. |

### xBTI

| Skill | Description |
|-------|-------------|
| [xbti-creator](skills/lovstudio-xbti-creator/) | Create custom BTI personality tests (LBTI, FBTI, etc.) with AI-generated content + avatars. |
| [xbti-gallery](skills/lovstudio-xbti-gallery/) | Browse all community-created BTI personality tests at xbti.lovstudio.ai. |

### Dev Tools

| Skill | Description |
|-------|-------------|
| [auto-context](skills/lovstudio-auto-context/) | Context hygiene checker. Suggests /fork or /btw when context is polluted. Best with [lovstudio plugin](https://github.com/lovstudio/claude-code-plugin) for auto-trigger. |
| [deploy-to-vercel](skills/lovstudio-deploy-to-vercel/) | Deploy frontend to Vercel with auto Cloudflare DNS + custom domain setup. |
| [project-port](skills/lovstudio-project-port/) | Generate stable unique dev port (3000–8999) from project name. |

## Related

**[lovstudio/claude-code-plugin](https://github.com/lovstudio/claude-code-plugin)** — Official Lovstudio plugin for Claude Code with hooks, commands, and auto-trigger support for skills like `auto-context`.

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=lovstudio/skills&type=Date)](https://star-history.com/#lovstudio/skills&Date)

## License

MIT &mdash; Made by [lovstudio.ai](https://lovstudio.ai)
