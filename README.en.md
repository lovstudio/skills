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

This repo is the **unified index** for the Lovstudio skills ecosystem. Every discoverable skill is
listed here. A skill is either mirrored under `skills/<name>/` in this repository or maintained in
an independent repo such as `lovstudio/{name}-skill`.

This repo contains:

- [`skills.yaml`](skills.yaml) — machine-readable manifest. Each skill has a terse `description` (Agent-facing trigger copy, CI-synced from the GitHub repo description) plus hand-maintained `tagline_en` / `tagline_zh` (the human-friendly one-liners you see in the table below).
- [`README.md`](README.md) / [`README.en.md`](README.en.md) — auto-rendered from the manifest.
- [`skills/`](skills) — installer-facing mirrors. Free skills are synced from their own repos; paid skills only expose public encrypted bundles or placeholders. Source code and history still live in each skill's own repo.

Skills marked ![Free](https://img.shields.io/badge/Free-green) install and run directly. Skills marked ![Paid](https://img.shields.io/badge/Paid-blueviolet) require sign-in and a Credits redemption; the installer downloads only an encrypted bundle, which is decrypted for an account with the entitlement. To purchase or ask questions, scan the QR code to follow the **手工川 (ShougongChuan)** WeChat official account:

<p align="center">
  <img src="assets/shougongchuan-banner.jpg" alt="Follow 手工川 on WeChat for paid skills" width="720">
</p>

## Skills

<!-- COUNT:START -->
> **84 skills** — 70 Free + 14 Paid.
<!-- COUNT:END -->

<!-- SKILLS:START -->
| | Skill | Description |
|---|---|---|
| **General** | | |
| ![Free](https://img.shields.io/badge/Free-green) | [`china-website-filing`](https://github.com/lovstudio/china-website-filing-skill) | Move a mainland China website from filing readiness through ICP, domain launch, public security filing, and verified compliance follow-up. |
| ![Free](https://img.shields.io/badge/Free-green) | [`describe-image`](https://github.com/lovstudio/describe-image-skill) | Give text-only models sight — describe any image via a free vision model. |
| ![Free](https://img.shields.io/badge/Free-green) | [`fact-check`](https://github.com/lovstudio/fact-check-skill) | Verify claims like a careful researcher, with primary sources, counterexamples, confidence, and next steps. — related: `image-translation-errata` |
| ![Free](https://img.shields.io/badge/Free-green) | [`hanzi-lens`](https://github.com/lovstudio/hanzi-lens-skill) | See one Chinese character through evidence — readings, form, history, classical context, meaning, and a professional visual. — requires: `professional-infographic` |
| ![Free](https://img.shields.io/badge/Free-green) | [`image-creator`](https://github.com/lovstudio/image-creator-skill) | Generate images through the right mechanism — AI, code rendering, or prompt tuning. — related: `professional-infographic`, `professional-portrait`, `image-translation-errata` |
| ![Free](https://img.shields.io/badge/Free-green) | [`image-translation-errata`](https://github.com/lovstudio/image-translation-errata-skill) | Expose bad machine translation, show the correction, and preserve the original image. — related: `translation-review`, `image-creator`, `fact-check` |
| ![Free](https://img.shields.io/badge/Free-green) | [`macos-disk-optimizer`](https://github.com/lovstudio/macos-disk-optimizer-skill) | Clean up Mac storage with guarded planning, archive migration, exact rollback-item purging, and real-capacity verification. |
| ![Free](https://img.shields.io/badge/Free-green) | [`media-crawler`](https://github.com/lovstudio/media-crawler-skill) | Turn an authorized social-media link into a verified local media file with resumable downloads and diagnostics. |
| ![Free](https://img.shields.io/badge/Free-green) | [`media-fetch`](https://github.com/lovstudio/media-fetch-skill) | Find the right edition, resume through the faster transport, and verify the local media and subtitle status. |
| ![Free](https://img.shields.io/badge/Free-green) | [`personal-vocabulary`](https://github.com/lovstudio/personal-vocabulary-skill) | One personal vocabulary reused across speech-input apps. |
| ![Paid](https://img.shields.io/badge/Paid-blueviolet) | [`subtitle-freedom`](https://github.com/lovstudio/subtitle-freedom-skill) | Make learner subtitles that keep the selected level and harder expressions, with spoiler-safe ASS cards and optional no-burn watermark sidecars. |
| ![Paid](https://img.shields.io/badge/Paid-blueviolet) | [`wdb-cli`](https://github.com/lovstudio/wdb-cli-skill) | Auto-discover WDB Pro managed keys and run precise local WeChat searches across chats, contacts, Moments, schemas, and exact records. |
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
| ![Free](https://img.shields.io/badge/Free-green) | [`business-card`](https://github.com/lovstudio/business-card-skill) | Turn anyone's name, roles and tagline into a polished editorial business card — high-res PNG plus a click-to-download HTML. |
| ![Paid](https://img.shields.io/badge/Paid-blueviolet) | [`event-poster`](https://github.com/lovstudio/event-poster-skill) | Turn an event brief into a polished poster, ready to share or print for exhibitions. |
| ![Free](https://img.shields.io/badge/Free-green) | [`find-logo`](https://github.com/lovstudio/find-logo-skill) | Collect brand logos from public sources — wide and transparent preferred, archived for website/PPT/poster lineups. |
| ![Free](https://img.shields.io/badge/Free-green) | [`maintain-partners`](https://github.com/lovstudio/maintain-partners-skill) | Scrape, normalize, and wire brand logos into the partners section across 4 locales in one shot. — requires: `find-logo` |
| ![Paid](https://img.shields.io/badge/Paid-blueviolet) | [`oh-my-landingpage`](https://github.com/lovstudio/oh-my-landingpage-skill) | Rebuild a landing page as one coherent brand experience, from the promise and story to the interface, media, and conversion path. |
| ![Paid](https://img.shields.io/badge/Paid-blueviolet) | [`professional-infographic`](https://github.com/lovstudio/professional-infographic-skill) | Turn dense material or an investment path into one sourced visual argument, from entry and staged exits to the decision that follows. — related: `image-creator` |
| ![Free](https://img.shields.io/badge/Free-green) | [`professional-portrait`](https://github.com/lovstudio/professional-portrait-skill) | Turn one photo into a clean, identity-preserving professional portrait. — related: `image-creator` |
| ![Paid](https://img.shields.io/badge/Paid-blueviolet) | [`visual-clone`](https://github.com/lovstudio/visual-clone-skill) | Extract the design DNA of a reference image so you can recreate the look. |
| **Academic** | | |
| ![Paid](https://img.shields.io/badge/Paid-blueviolet) | [`academic-translator`](https://github.com/lovstudio/academic-translator-skill) | Translate English papers into Chinese while preserving figures, equations, pages, and navigation. |
| ![Paid](https://img.shields.io/badge/Paid-blueviolet) | [`paper-translator`](https://github.com/lovstudio/paper-translator-skill) | Translate academic PDFs into Chinese with matched pages, bilingual layouts, figures, and formulas. |
| ![Free](https://img.shields.io/badge/Free-green) | [`thesis-polish`](https://github.com/lovstudio/thesis-polish-skill) | Polish an MBA thesis across language, structure, argument, and originality. |
| ![Free](https://img.shields.io/badge/Free-green) | [`translation-review`](https://github.com/lovstudio/translation-review-skill) | Review a Chinese→English translation against the original across six quality dimensions. — related: `image-translation-errata` |
| **Office Automation** | | |
| ![Free](https://img.shields.io/badge/Free-green) | [`any2deck`](https://github.com/lovstudio/any2deck-skill) | Turn any content into a styled slide deck — 16 looks, export to PPTX or PDF. — related: `any2pdf`, `any2docx` |
| ![Free](https://img.shields.io/badge/Free-green) | [`any2docx`](https://github.com/lovstudio/any2docx-skill) | Convert Markdown into a clean, professionally styled Word document. — related: `any2pdf`, `any2deck` |
| ![Free](https://img.shields.io/badge/Free-green) | [`any2pdf`](https://github.com/lovstudio/any2pdf-skill) | Typeset Markdown into a publication-quality PDF with 16 themes, including Songti Reading. — related: `any2docx`, `any2deck` |
| ![Free](https://img.shields.io/badge/Free-green) | [`fill-form`](https://github.com/lovstudio/fill-form-skill) | Fill Word (.docx) form templates automatically, with clean CJK typography. |
| ![Free](https://img.shields.io/badge/Free-green) | [`fill-web-form`](https://github.com/lovstudio/fill-web-form-skill) | Answer online forms using your own knowledge base as the source of truth. |
| ![Free](https://img.shields.io/badge/Free-green) | [`pdf2png`](https://github.com/lovstudio/pdf2png-skill) | Convert a PDF to a single long PNG — fast enough to feel instant on macOS. |
| ![Free](https://img.shields.io/badge/Free-green) | [`png2svg`](https://github.com/lovstudio/png2svg-skill) | Convert a PNG to a crisp SVG, with background removed and curves smoothed. |
| ![Free](https://img.shields.io/badge/Free-green) | [`rich-export`](https://github.com/lovstudio/rich-export-skill) | Export one rich-media source into web, editable document, print, and archive formats. |
| ![Free](https://img.shields.io/badge/Free-green) | [`yoda-automation`](https://github.com/lovstudio/yoda-automation-skill) | Create reliable Yoda reminders and recurring follow-ups with verified schedules, run evidence, and a precise stop rule. |
| **Content Creation** | | |
| ![Free](https://img.shields.io/badge/Free-green) | [`anti-wechat-ai-check`](https://github.com/lovstudio/anti-wechat-ai-check-skill) | Detect AI fingerprints in an article and rewrite it to read like a human. |
| ![Free](https://img.shields.io/badge/Free-green) | [`deep-research`](https://github.com/lovstudio/deep-research-skill) | Produce citation-tracked research reports with persistent evidence, claim verification, and Markdown/HTML/PDF packaging. |
| ![Free](https://img.shields.io/badge/Free-green) | [`document-illustrator`](https://github.com/lovstudio/document-illustrator-skill) | Illustrate a long document in place — plan, generate, and insert images automatically. — requires: `image-creator` |
| ![Free](https://img.shields.io/badge/Free-green) | [`style-clone`](https://github.com/lovstudio/style-clone-skill) | Extract a writing style profile from sample articles, then rewrite any content in that style. |
| ![Paid](https://img.shields.io/badge/Paid-blueviolet) | [`wechat-article-branding`](https://github.com/lovstudio/wechat-article-branding-skill) | Turn a WeChat article into one coherent branded edition with an editorial art cover, centered publisher Logo, reusable prompt, and real-page acceptance. — related: `wechat-article-operator` |
| ![Paid](https://img.shields.io/badge/Paid-blueviolet) | [`wechat-article-operator`](https://github.com/lovstudio/wechat-article-operator-skill) | Read and edit an existing WeChat article with persisted-state verification, from exact content changes to cover replacement. — related: `wechat-article-branding` |
| ![Paid](https://img.shields.io/badge/Paid-blueviolet) | [`write-professional-book`](https://github.com/lovstudio/write-professional-book-skill) | Write a full multi-chapter book — technical, tutorial, or monograph — from an outline. |
| ![Paid](https://img.shields.io/badge/Paid-blueviolet) | [`wxmp-cracker`](https://github.com/lovstudio/wxmp-cracker-skill) | Archive WeChat Official Account articles into clean, reusable text. |
| **Dev Tools** | | |
| ![Free](https://img.shields.io/badge/Free-green) | [`app-generator`](https://github.com/lovstudio/app-generator-skill) | Generate Lovstudio-grade web, PWA, or Tauri apps with brand, UI, data, deploy/release, and developer tooling wired in. |
| ![Free](https://img.shields.io/badge/Free-green) | [`ataru-indexing`](https://github.com/lovstudio/ataru-indexing-skill) | Make sure your local AI session memory is actually searchable before you search it. |
| ![Free](https://img.shields.io/badge/Free-green) | [`ataru-search`](https://github.com/lovstudio/ataru-search-skill) | Find what you and your AI already worked out, and read it back in its original context. |
| ![Free](https://img.shields.io/badge/Free-green) | [`auto-context`](https://github.com/lovstudio/auto-context-skill) | Watch your Claude Code context for pollution and suggest when to fork or reset. |
| ![Free](https://img.shields.io/badge/Free-green) | [`cc-migrate-session`](https://github.com/lovstudio/cc-migrate-session) | Keep your Claude Code session history working after you move a project folder. |
| ![Free](https://img.shields.io/badge/Free-green) | [`clash-tun-doctor`](https://github.com/lovstudio/clash-tun-doctor-skill) | Diagnose Clash TUN failures from runtime evidence, apply reversible fixes, and verify the real application path. |
| ![Free](https://img.shields.io/badge/Free-green) | [`deploy-to-vercel`](https://github.com/lovstudio/deploy-to-vercel-skill) | Ship a frontend to Vercel with custom domain and Cloudflare DNS wired up automatically. |
| ![Free](https://img.shields.io/badge/Free-green) | [`dsh-plugin-creator`](https://github.com/lovstudio/dsh-plugin-creator-skill) | Author a DSH plugin end-to-end — pick the extension point, scaffold, implement, and pass the repo gates. — related: `dsh-plugin-publisher` |
| ![Free](https://img.shields.io/badge/Free-green) | [`dsh-plugin-publisher`](https://github.com/lovstudio/dsh-plugin-publisher-skill) | Publish a validated DSH plugin across npm, git, and tarball channels with per-channel load evidence. — related: `dsh-plugin-creator` |
| ![Free](https://img.shields.io/badge/Free-green) | [`electron-app-relaunch`](https://github.com/lovstudio/electron-app-relaunch-skill) | Add a real Electron relaunch while keeping renderer reload and update handoff separate. |
| ![Free](https://img.shields.io/badge/Free-green) | [`electron-delta-updater`](https://github.com/lovstudio/electron-delta-updater-skill) | Build verified Electron delta updates with Sparkle, appcasts, signing, and installation proof. |
| ![Free](https://img.shields.io/badge/Free-green) | [`finder-action`](https://github.com/lovstudio/finder-action-skill) | Add a custom right-click action to macOS Finder in minutes. |
| ![Free](https://img.shields.io/badge/Free-green) | [`gh-access`](https://github.com/lovstudio/gh-access-skill) | Grant, revoke, or audit collaborator access on private GitHub repos in one command. |
| ![Free](https://img.shields.io/badge/Free-green) | [`gh-contribute`](https://github.com/lovstudio/gh-contribute-skill) | Ship a clean PR to any upstream GitHub repo — fork, branch, push, and open PR for you. |
| ![Free](https://img.shields.io/badge/Free-green) | [`gh-tidy`](https://github.com/lovstudio/gh-tidy-skill) | Triage and clean up GitHub issues, PRs, branches, and labels in a single pass. |
| ![Free](https://img.shields.io/badge/Free-green) | [`install-ai`](https://github.com/lovstudio/install-ai-skill) | Add an App AI feature with Agent Client, MaaS routing, model intent, and optional UI. |
| ![Free](https://img.shields.io/badge/Free-green) | [`install-tanstack-query`](https://github.com/lovstudio/install-tanstack-query-skill) | Initialize TanStack Query and migrate request state into shared query keys and hooks. |
| ![Free](https://img.shields.io/badge/Free-green) | [`integrate-lovinsp`](https://github.com/lovstudio/integrate-lovinsp-skill) | Click a page element in dev and jump straight to its source. |
| ![Free](https://img.shields.io/badge/Free-green) | [`mobile-adapt`](https://github.com/lovstudio/mobile-adapt-skill) | Scan a web project for mobile issues and fix them — overflow, safe area, viewport units, responsive layouts, and page navigation. |
| ![Free](https://img.shields.io/badge/Free-green) | [`npm-publisher`](https://github.com/lovstudio/lov-npm-publisher-skill) | Publish npm packages without repeated login — OIDC trusted publishing or a local NPM_TOKEN. |
| ![Free](https://img.shields.io/badge/Free-green) | [`obsidian-reset-cache`](https://github.com/lovstudio/obsidian-reset-cache-skill) | Reset Obsidian's cache when it gets stuck on "Loading cache". |
| ![Free](https://img.shields.io/badge/Free-green) | [`optimize-tauri-backend`](https://github.com/lovstudio/optimize-tauri-backend-skill) | Reduce Tauri Rust restart pain by modularizing the backend, shrinking command surfaces, and hardening long IPC streams. |
| ![Free](https://img.shields.io/badge/Free-green) | [`project-port`](https://github.com/lovstudio/project-port-skill) | Assign each project a stable, unique dev port so services stop colliding. |
| ![Free](https://img.shields.io/badge/Free-green) | [`release-via-cicd`](https://github.com/lovstudio/release-via-cicd-skill) | Configure release workflows, publish versions, and verify signed Tauri app artifacts. |
| ![Free](https://img.shields.io/badge/Free-green) | [`repo2docs`](https://github.com/lovstudio/repo2docs-skill) | Turn any folder — code, articles, images — into a polished Fumadocs site, built incrementally and shipped to {id}.lovstudio.ai/docs. |
| ![Free](https://img.shields.io/badge/Free-green) | [`skill-distiller`](https://github.com/lovstudio/skill-distiller-skill) | Turn delivery history into a clear, reusable Skill blueprint with boundaries and acceptance checks. |
| ![Free](https://img.shields.io/badge/Free-green) | [`skill-pricing`](https://github.com/lovstudio/skill-pricing-skill) | Turn Skill pricing into an explainable decision backed by cost, value, confidence, and channel fit. |
| ![Free](https://img.shields.io/badge/Free-green) | [`skill-publisher`](https://github.com/lovstudio/skill-publisher-skill) | Price by default, then publish a validated Skill across channels with independently verifiable release states. — requires: `skill-pricing` |
| **Video Creation** | | |
| ![Free](https://img.shields.io/badge/Free-green) | [`media-creator`](https://github.com/lovstudio/media-creator-skill) | Turn real screen recordings into publish-ready videos with protected result audio, BGM mix, cover direction, and delivery evidence. |
| ![Free](https://img.shields.io/badge/Free-green) | [`publish-wechat-channels`](https://github.com/lovstudio/publish-wechat-channels-skill) | Publish WeChat Channels videos with preflight, field readback, and status verification. |
| ![Free](https://img.shields.io/badge/Free-green) | [`video-chapter`](https://github.com/lovstudio/video-chapter-skill) | Plan chapters, tune the progress bar in React Studio, then export an overlay, final video, or editor package. |
| **Meta** | | |
| ![Free](https://img.shields.io/badge/Free-green) | [`skill-creator`](https://github.com/lovstudio/skill-creator-skill) | Scaffold a new skill as an independent source repo with release-driven aggregate distribution. |
| ![Free](https://img.shields.io/badge/Free-green) | [`skill-optimizer`](https://github.com/lovstudio/skill-optimizer-skill) | Audit an existing skill, auto-fix issues, and bump its version in one pass. |
<!-- SKILLS:END -->

<sub>The table above is auto-generated from [`skills.yaml`](skills.yaml) by [`scripts/render-readme.py`](scripts/render-readme.py). Edit `skills.yaml`, not this table.</sub>

## Install

Single entry point — `npx lovstudio` covers the unified catalog:

```bash
# install one skill
npx lovstudio skills add any2pdf

# install all free skills; add paid skills individually
npx lovstudio skills add skills

# paid skill — sign in and redeem with Credits
npx lovstudio skills add proposal
```

Free skills install directly. Paid skills complete sign-in and Credits redemption before downloading
the encrypted bundle; add `-y` in CI or other non-interactive environments.

Browse and install via [agentskills.io](https://agentskills.io) for a one-click experience.

## How It Works

```
lovstudio/skills (this repo)         ← unified Lovstudio skills ecosystem index
├── README.md                        ← primary top-level index (简体中文, default)
├── README.en.md                     ← English index
└── skills/<name>/                    ← free mirror or encrypted paid bundle

lovstudio/<name>-skill               ← regular skill source repo
├── SKILL.md                         ← skill definition (frontmatter + docs)
├── scripts/                         ← implementation (Python/Shell/Node)
├── README.md                        ← per-skill install & usage
└── examples/ · references/          ← optional assets

```

The **`paid` field** lives in `skills.yaml` (this repo), not in each SKILL.md — it's a business categorization, not a skill property. Paid skill code is private; public trigger info (name, tagline, category) is still indexed here so agentskills.io can display and prompt purchase.

## Contributing

- **New skill**: use [`skill-creator`](https://github.com/lovstudio/skill-creator-skill) to scaffold. Put it directly under `skills/<name>/` or create an independent `lovstudio/{name}-skill` repo, then register it in this repo's `skills.yaml`.
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
