<h1 align="center">Lovstudio Skills</h1>

<p align="center">
  <strong>Central index of all Lovstudio AI coding skills for Claude Code.</strong><br>
  <sub>By <a href="https://lovstudio.ai">Lovstudio</a> · <a href="https://agentskills.io">agentskills.io</a></sub>
</p>

<p align="center">
  <a href="README.md">简体中文</a> · <b>English</b>
</p>

<p align="center">
  <a href="#skills">Skills</a> ·
  <a href="#install">Install</a> ·
  <a href="#how-it-works">How It Works</a> ·
  <a href="#contributing">Contributing</a> ·
  <a href="#license">License</a>
</p>

---

## What Is This

This repo is the **central index** for Lovstudio skills. Each skill lives in its own repo at `github.com/lovstudio/{name}-skill`. This repo contains:

- [`skills.yaml`](skills.yaml) — machine-readable manifest. Each skill has a terse `description` (Agent-facing trigger copy, CI-synced from the GitHub repo description) plus hand-maintained `tagline_en` / `tagline_zh` (the human-friendly one-liners you see in the table below).
- [`README.md`](README.md) / [`README.en.md`](README.en.md) — auto-rendered from the manifest.
- No code. Skill code and history live in their individual repos.

Skills marked ![Free](https://img.shields.io/badge/Free-green) are open source (MIT). Skills marked ![Paid](https://img.shields.io/badge/Paid-blueviolet) are commercial — private repo, purchase required. To purchase or ask questions, scan the QR code to follow the **手工川 (ShougongChuan)** WeChat official account:

<p align="center">
  <img src="assets/shougongchuan-banner.jpg" alt="Follow 手工川 on WeChat for paid skills" width="720">
</p>

## Skills

<!-- COUNT:START -->
> **21 skills** — 15 Free + 6 Paid.
<!-- COUNT:END -->

<!-- SKILLS:START -->
| | Skill | Description |
|---|---|---|
| **General** | | |
| ![Free](https://img.shields.io/badge/Free-green) | [`image-creator`](https://github.com/lovstudio/image-creator-skill) | Generate images through the right mechanism — AI, code rendering, or prompt tuning. |
| **Business** | | |
| ![Paid](https://img.shields.io/badge/Paid-blueviolet) | [`proposal`](https://github.com/lovstudio/proposal-skill) | Turn a project brief into a complete, client-ready business proposal. |
| ![Paid](https://img.shields.io/badge/Paid-blueviolet) | [`review-doc`](https://github.com/lovstudio/review-doc-skill) | Review a document or contract and return it with inline comments. |
| **Design** | | |
| ![Paid](https://img.shields.io/badge/Paid-blueviolet) | [`event-poster`](https://github.com/lovstudio/event-poster-skill) | Turn an event brief into a polished poster, ready to share. |
| ![Free](https://img.shields.io/badge/Free-green) | [`find-logo`](https://github.com/lovstudio/find-logo-skill) | Collect brand logos from public sources — wide and transparent preferred, archived for website/PPT/poster lineups. |
| ![Free](https://img.shields.io/badge/Free-green) | [`visual-clone`](https://github.com/lovstudio/visual-clone-skill) | Extract the design DNA of a reference image so you can recreate the look. |
| **Academic** | | |
| ![Free](https://img.shields.io/badge/Free-green) | [`thesis-polish`](https://github.com/lovstudio/thesis-polish-skill) | Polish an MBA thesis across language, structure, argument, and originality. |
| ![Free](https://img.shields.io/badge/Free-green) | [`translation-review`](https://github.com/lovstudio/translation-review-skill) | Review a Chinese→English translation against the original across six quality dimensions. |
| **Office Automation** | | |
| ![Free](https://img.shields.io/badge/Free-green) | [`any2deck`](https://github.com/lovstudio/any2deck-skill) | Turn any content into a styled slide deck — 16 looks, export to PPTX or PDF. — related: `any2pdf`, `any2docx` |
| ![Free](https://img.shields.io/badge/Free-green) | [`any2docx`](https://github.com/lovstudio/any2docx-skill) | Convert Markdown into a clean, professionally styled Word document. — related: `any2pdf`, `any2deck` |
| ![Free](https://img.shields.io/badge/Free-green) | [`any2pdf`](https://github.com/lovstudio/any2pdf-skill) | Typeset Markdown into a publication-quality PDF with 14 built-in themes. — related: `any2docx`, `any2deck` |
| ![Free](https://img.shields.io/badge/Free-green) | [`fill-form`](https://github.com/lovstudio/fill-form-skill) | Fill Word (.docx) form templates automatically, with clean CJK typography. |
| ![Free](https://img.shields.io/badge/Free-green) | [`fill-web-form`](https://github.com/lovstudio/fill-web-form-skill) | Answer online forms using your own knowledge base as the source of truth. |
| ![Free](https://img.shields.io/badge/Free-green) | [`pdf2png`](https://github.com/lovstudio/pdf2png-skill) | Convert a PDF to a single long PNG — fast enough to feel instant on macOS. |
| ![Free](https://img.shields.io/badge/Free-green) | [`png2svg`](https://github.com/lovstudio/png2svg-skill) | Convert a PNG to a crisp SVG, with background removed and curves smoothed. |
| **Finance** | | |
| ![Free](https://img.shields.io/badge/Free-green) | [`expense-report`](https://github.com/lovstudio/expense-report-skill) | Turn a pile of invoices into a categorized Excel expense report. |
| **Content Creation** | | |
| ![Free](https://img.shields.io/badge/Free-green) | [`anti-wechat-ai-check`](https://github.com/lovstudio/anti-wechat-ai-check-skill) | Detect AI fingerprints in an article and rewrite it to read like a human. |
| ![Free](https://img.shields.io/badge/Free-green) | [`document-illustrator`](https://github.com/lovstudio/document-illustrator-skill) | Illustrate a long document in place — plan, generate, and insert images automatically. — requires: `image-creator` |
| ![Paid](https://img.shields.io/badge/Paid-blueviolet) | [`event-curator`](https://github.com/lovstudio/event-curator-skill) | Turn a guest bio into a ready-to-run event plan — title, rundown, host questions, and gifts. |
| ![Paid](https://img.shields.io/badge/Paid-blueviolet) | [`write-professional-book`](https://github.com/lovstudio/write-professional-book-skill) | Write a full multi-chapter book — technical, tutorial, or monograph — from an outline. |
| ![Paid](https://img.shields.io/badge/Paid-blueviolet) | [`wxmp-cracker`](https://github.com/lovstudio/wxmp-cracker-skill) | Archive WeChat Official Account articles into clean, reusable text. |
<!-- SKILLS:END -->

<sub>The table above is auto-generated from [`skills.yaml`](skills.yaml) by [`scripts/render-readme.py`](scripts/render-readme.py). Edit `skills.yaml`, not this table.</sub>

## Extension indexes

The following thematic skills live in their own sub-index repos, each with its own manifest and mirror. Install as needed:

| Sub-index | Scope | Install |
|---|---|---|
| [`lovstudio/dev-skills`](https://github.com/lovstudio/dev-skills) | Developer & skill-author tools: Meta (skill-creator / skill-optimizer) + Dev Tools (GitHub, Vercel, macOS, Claude Code session, …) | `npx skills add lovstudio/dev-skills --all -g` |
| [`lovstudio/xbti-skills`](https://github.com/lovstudio/xbti-skills) | Build and browse xBTI personality tests (paired with [xbti.lovstudio.ai](https://xbti.lovstudio.ai)) | `npx skills add lovstudio/xbti-skills --all -g` |

## Install

**Recommended: install all free skills globally for Claude Code** (AI-friendly, no interactive prompts):

```bash
npx skills add lovstudio/skills --all -g
```

> `--all` expands to `--skill '*' --agent '*' -y`; `-g` installs into `~/.claude/skills/`. Without these flags the CLI opens three interactive prompts (pick skills → pick agents → confirm), which hang in AI/CI/non-TTY environments.

**Install a single skill**:

```bash
npx skills add lovstudio/skills --skill any2pdf -g -y
```

**Or clone manually** (paid skills after purchase with your authorized SSH key):

```bash
git clone https://github.com/lovstudio/any2pdf-skill ~/.claude/skills/lovstudio-any2pdf
git clone git@github.com:lovstudio/write-professional-book-skill ~/.claude/skills/lovstudio-write-professional-book
```

Browse and install via [agentskills.io](https://agentskills.io) for a one-click experience.

## How It Works

```
lovstudio/skills (this repo)         ← you are here
├── README.md                        ← human-readable index (简体中文, default)
├── README.en.md                     ← English index
├── skills.yaml                      ← machine-readable manifest
└── .github/workflows/               ← CI: renders READMEs, syncs descriptions

lovstudio/<name>-skill               ← each skill, independent repo
├── SKILL.md                         ← skill definition (frontmatter + docs)
├── scripts/                         ← implementation (Python/Shell/Node)
├── README.md                        ← per-skill install & usage
└── examples/ · references/          ← optional assets
```

The **`paid` field** lives in `skills.yaml` (this repo), not in each SKILL.md — it's a business categorization, not a skill property. Paid skill code is private; public trigger info (name, tagline, category) is still indexed here so agentskills.io can display and prompt purchase.

## Contributing

- **New skill**: use [`skill-creator`](https://github.com/lovstudio/skill-creator-skill) to scaffold. Then create a repo at `lovstudio/{name}-skill` and open a PR here adding it to `skills.yaml`.
- **Existing skill**: file issues / PRs in the skill's own repo.
- **Index fixes** (categorization, descriptions, links): PR against this repo's `skills.yaml`. **Don't touch the README table** — CI regenerates it.

## License

- **This index repo**: MIT
- **Free skills**: MIT (see each repo's LICENSE)
- **Paid skills**: commercial license — see the skill's purchase page

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=lovstudio/skills&type=Date)](https://star-history.com/#lovstudio/skills&Date)

---

<p align="center">
  <sub>Built with <a href="https://claude.com/claude-code">Claude Code</a> · by <a href="https://lovstudio.ai">Lovstudio</a></sub>
</p>
