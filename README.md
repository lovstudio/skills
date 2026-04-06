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
  <a href="#theme-gallery">Theme Gallery</a>
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

| Skill | Description |
|-------|-------------|
| [any2deck](skills/lovstudio-any2deck/) | Content → slide deck images with 16 styles, PPTX/PDF export, branding overlay. |
| [any2docx](skills/lovstudio-any2docx/) | Markdown → professionally styled DOCX (Word). Same themes as any2pdf, editable output. |
| [any2pdf](skills/lovstudio-any2pdf/) | Markdown → professionally typeset PDF. CJK/Latin mixed text, code blocks, tables, 14 themes. |
| [fill-form](skills/lovstudio-fill-form/) | Fill Word form templates (.docx). Auto-detects table fields, CJK font support. |
| [skill-creator](skills/lovstudio-skill-creator/) | Scaffold new lovstudio skills with proper structure, SKILL.md + README.md. |

## Theme Gallery

Both skills share the same set of 14 color themes. Here's how they look:

### Light Themes

| warm-academic | nord-frost | github-light | solarized-light |
|:---:|:---:|:---:|:---:|
| ![warm-academic](docs/previews/warm-academic.png) | ![nord-frost](docs/previews/nord-frost.png) | ![github-light](docs/previews/github-light.png) | ![solarized-light](docs/previews/solarized-light.png) |

| paper-classic | ocean-breeze | tufte | classic-thesis |
|:---:|:---:|:---:|:---:|
| ![paper-classic](docs/previews/paper-classic.png) | ![ocean-breeze](docs/previews/ocean-breeze.png) | ![tufte](docs/previews/tufte.png) | ![classic-thesis](docs/previews/classic-thesis.png) |

| ieee-journal | elegant-book | chinese-red | ink-wash |
|:---:|:---:|:---:|:---:|
| ![ieee-journal](docs/previews/ieee-journal.png) | ![elegant-book](docs/previews/elegant-book.png) | ![chinese-red](docs/previews/chinese-red.png) | ![ink-wash](docs/previews/ink-wash.png) |

### Dark Themes

| monokai-warm | dracula-soft |
|:---:|:---:|
| ![monokai-warm](docs/previews/monokai-warm.png) | ![dracula-soft](docs/previews/dracula-soft.png) |

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=lovstudio/skills&type=Date)](https://star-history.com/#lovstudio/skills&Date)

## License

MIT &mdash; Made by [lovstudio.ai](https://lovstudio.ai)
