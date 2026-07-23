<h1 align="center">Lovstudio Skills</h1>

<p align="center">
  <strong>Top-level index for the Lovstudio AI coding skills ecosystem.</strong><br>
  <sub>By <a href="https://lovstudio.ai">Lovstudio</a> · <a href="https://agentskills.io">agentskills.io</a></sub>
</p>

<p align="center">
  <a href="README.md">简体中文</a> · <b>English</b>
</p>

<p align="center">
  <a href="#skills">Skills</a> ·
  <a href="#extension-indexes">Extension indexes</a> ·
  <a href="#install">Install</a> ·
  <a href="#how-it-works">How It Works</a> ·
  <a href="#contributing">Contributing</a> ·
  <a href="#license">License</a>
</p>

---

## What Is This

This repo is the **top-level index** for the Lovstudio skills ecosystem. General skills now live in
[`lovstudio/general-skills`](https://github.com/lovstudio/general-skills); developer tooling, xBTI,
and other themed collections are linked below as extension index repos.

For backwards compatibility, this repo temporarily keeps the general-skills manifest and install
mirror. New general-skill updates should go to `lovstudio/general-skills`.

This repo contains:

- [`skills.yaml`](skills.yaml) — machine-readable manifest. Each skill has a terse `description` (Agent-facing trigger copy, CI-synced from the GitHub repo description) plus hand-maintained `tagline_en` / `tagline_zh` (the human-friendly one-liners you see in the table below).
- [`README.md`](README.md) / [`README.en.md`](README.en.md) — auto-rendered from the manifest.
- [`skills/`](skills) — installer-facing mirrors. Free skills are synced from their own repos; paid skills only expose public encrypted bundles or placeholders. Source code and history still live in each skill's own repo.

Skills marked ![Free](https://img.shields.io/badge/Free-green) are open source (MIT). Skills marked ![Paid](https://img.shields.io/badge/Paid-blueviolet) are commercial — private repo, purchase required. To purchase or ask questions, scan the QR code to follow the **手工川 (ShougongChuan)** WeChat official account:

<p align="center">
  <img src="assets/shougongchuan-banner.jpg" alt="Follow 手工川 on WeChat for paid skills" width="720">
</p>

## Skills

<!-- COUNT:START -->
> **30 skills** — 24 Free + 6 Paid.
<!-- COUNT:END -->

<!-- SKILLS:START -->
| | Skill | Description |
|---|---|---|
| **General** | | |
| ![Free](https://img.shields.io/badge/Free-green) | [`image-creator`](https://github.com/lovstudio/image-creator-skill) | Generate images through the right mechanism — AI, code rendering, or prompt tuning. |
| **Business** | | |
| ![Free](https://img.shields.io/badge/Free-green) | [`bp`](https://github.com/lovstudio/bp-skill) | A composable BP skill kit — use outline, deck, and polish alone or run the complete investor workflow. — requires: `bp-outline`, `bp-deck`, `bp-polish` |
| ![Free](https://img.shields.io/badge/Free-green) | [`bp-deck`](https://github.com/lovstudio/bp-skill) | Turn an approved BP outline into a professional PPTX, PDF, and full-deck preview with deliberate style selection. — requires: `any2deck` |
| ![Free](https://img.shields.io/badge/Free-green) | [`bp-outline`](https://github.com/lovstudio/bp-skill) | Turn project evidence into an investor narrative and a source-backed 12–15 slide outline before making PPT. |
| ![Free](https://img.shields.io/badge/Free-green) | [`bp-polish`](https://github.com/lovstudio/bp-skill) | Audit and polish an existing BP with a scored report and page-level fixes—without changing the facts. |
| ![Free](https://img.shields.io/badge/Free-green) | [`contract-review-pro`](https://github.com/lovstudio/contract-review-pro-skill) | Professional-grade contract review — four-layer methodology, structured comments with risk levels, summary, opinion, and business flowchart. |
| ![Paid](https://img.shields.io/badge/Paid-blueviolet) | [`event-curator`](https://github.com/lovstudio/event-curator-skill) | Turn a guest bio into a ready-to-run event plan — title, rundown, host questions, and gifts. |
| ![Free](https://img.shields.io/badge/Free-green) | [`expense-report`](https://github.com/lovstudio/expense-report-skill) | Turn a pile of invoices into a categorized Excel expense report. |
| ![Paid](https://img.shields.io/badge/Paid-blueviolet) | [`proposal`](https://github.com/lovstudio/proposal-skill) | Turn a project brief into a complete, client-ready business proposal. |
| ![Free](https://img.shields.io/badge/Free-green) | [`review-doc`](https://github.com/lovstudio/review-doc-skill) | Review a document or contract and return it with inline comments. |
| ![Free](https://img.shields.io/badge/Free-green) | [`solution-architect`](https://github.com/lovstudio/solution-architect-skill) | Turn a product or technical requirement into a researched, open-source-first implementation plan. |
| **Design** | | |
| ![Paid](https://img.shields.io/badge/Paid-blueviolet) | [`event-poster`](https://github.com/lovstudio/event-poster-skill) | Turn an event brief into a polished poster, ready to share or print for exhibitions. |
| ![Free](https://img.shields.io/badge/Free-green) | [`find-logo`](https://github.com/lovstudio/find-logo-skill) | Collect brand logos from public sources — wide and transparent preferred, archived for website/PPT/poster lineups. |
| ![Free](https://img.shields.io/badge/Free-green) | [`maintain-partners`](https://github.com/lovstudio/maintain-partners-skill) | Scrape, normalize, and wire brand logos into the partners section across 4 locales in one shot. |
| ![Paid](https://img.shields.io/badge/Paid-blueviolet) | [`visual-clone`](https://github.com/lovstudio/visual-clone-skill) | Extract the design DNA of a reference image so you can recreate the look. |
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
| **Content Creation** | | |
| ![Free](https://img.shields.io/badge/Free-green) | [`anti-wechat-ai-check`](https://github.com/lovstudio/anti-wechat-ai-check-skill) | Detect AI fingerprints in an article and rewrite it to read like a human. |
| ![Free](https://img.shields.io/badge/Free-green) | [`deep-research`](https://github.com/lovstudio/deep-research-skill) | Produce citation-tracked research reports with persistent evidence, claim verification, and Markdown/HTML/PDF packaging. |
| ![Free](https://img.shields.io/badge/Free-green) | [`document-illustrator`](https://github.com/lovstudio/document-illustrator-skill) | Illustrate a long document in place — plan, generate, and insert images automatically. — requires: `image-creator` |
| ![Free](https://img.shields.io/badge/Free-green) | [`style-clone`](https://github.com/lovstudio/style-clone-skill) | Extract a writing style profile from sample articles, then rewrite any content in that style. |
| ![Paid](https://img.shields.io/badge/Paid-blueviolet) | [`write-professional-book`](https://github.com/lovstudio/write-professional-book-skill) | Write a full multi-chapter book — technical, tutorial, or monograph — from an outline. |
| ![Paid](https://img.shields.io/badge/Paid-blueviolet) | [`wxmp-cracker`](https://github.com/lovstudio/wxmp-cracker-skill) | Archive WeChat Official Account articles into clean, reusable text. |
<!-- SKILLS:END -->

<sub>The table above is auto-generated from [`skills.yaml`](skills.yaml) by [`scripts/render-readme.py`](scripts/render-readme.py). Edit `skills.yaml`, not this table.</sub>

## Extension indexes

The following thematic skills live in their own sub-index repos, each with its own manifest and
mirror. They are still part of the Lovstudio skills ecosystem, but they are not expanded one by one
in the regular skills table above. Install as needed:

| Sub-index | Scope | Install |
|---|---|---|
| [`lovstudio/general-skills`](https://github.com/lovstudio/general-skills) | General Lovstudio skills: office automation, business, design, academic, content creation, and more | `npx lovstudio skills add general-skills -g -y` |
| [`lovstudio/dev-skills`](https://github.com/lovstudio/dev-skills) | Developer & skill-author tools: Meta (skill-creator / skill-optimizer) + Dev Tools (GitHub, Vercel, macOS, Claude Code session, TanStack Query setup/refactors, …) | `npx lovstudio skills add dev-skills -g -y` |
| [`lovstudio/xbti-skills`](https://github.com/lovstudio/xbti-skills) | Build and browse xBTI personality tests (paired with [xbti.lovstudio.ai](https://xbti.lovstudio.ai)) | `npx lovstudio skills add xbti-skills -g -y` |

## Install

Single entry point — `npx lovstudio` covers free and paid skills alike:

```bash
# install one skill
npx lovstudio skills add any2pdf -g -y

# install all general skills
npx lovstudio skills add general-skills -g -y

# paid skill — install + activate license in one shot
npx lovstudio skills add proposal -k lk-<your-license-key> -g -y

# activate license alone (for skills you already installed)
npx lovstudio license activate lk-<your-license-key>
```

> `-g` installs into `~/.claude/skills/`, `-y` skips confirmation (required in AI/CI/non-TTY environments).

Browse and install via [agentskills.io](https://agentskills.io) for a one-click experience.

## How It Works

```
lovstudio/skills (this repo)         ← top-level Lovstudio skills ecosystem index
├── README.md                        ← primary top-level index (简体中文, default)
├── README.en.md                     ← English index
└── README / extension index links   ← points to general/dev/xBTI sub-indexes

lovstudio/general-skills             ← general skills index + install mirror
├── skills.yaml
├── skills/<name>/
└── .claude-plugin/marketplace.json

lovstudio/<name>-skill               ← regular skill source repo
├── SKILL.md                         ← skill definition (frontmatter + docs)
├── scripts/                         ← implementation (Python/Shell/Node)
├── README.md                        ← per-skill install & usage
└── examples/ · references/          ← optional assets

lovstudio/dev-skills                 ← developer / skill-author tooling sub-index
└── skills/<name>/                   ← bundled dev/meta skills
```

The **`paid` field** lives in `skills.yaml` (this repo), not in each SKILL.md — it's a business categorization, not a skill property. Paid skill code is private; public trigger info (name, tagline, category) is still indexed here so agentskills.io can display and prompt purchase.

## Contributing

- **New regular skill**: use [`skill-creator`](https://github.com/lovstudio/skill-creator-skill) to scaffold. Then create a repo at `lovstudio/{name}-skill` and open a PR against [`lovstudio/general-skills`](https://github.com/lovstudio/general-skills) adding it to `skills.yaml`.
- **New developer/meta skill**: prefer [`lovstudio/dev-skills`](https://github.com/lovstudio/dev-skills), where that sub-index owns its `skills.yaml`, README, and mirror.
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
