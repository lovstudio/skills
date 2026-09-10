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
> **165 skills** — 149 Free + 16 Paid.
<!-- COUNT:END -->

<!-- SKILLS:START -->
| | Skill | Description |
|---|---|---|
| **General** | | |
| ![Free](https://img.shields.io/badge/Free-green) | [Requirements Compass](https://github.com/lovstudio/skills) (`brainstorm`) | Help clarify requirements through brainstorming — requires: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Website Filing Assistant](https://github.com/lovstudio/china-website-filing-skill) (`china-website-filing`) | Move a mainland China website from filing readiness through ICP, domain launch, public security filing, and verified compliance follow-up. |
| ![Paid](https://img.shields.io/badge/Paid-blueviolet) | [Mac Cleaner](https://github.com/lovstudio/macos-disk-optimizer-skill) (`clean-mac`) | Clean up Mac storage without touching protected app workspaces, with guarded migration, rollback, and real-capacity verification. |
| ![Free](https://img.shields.io/badge/Free-green) | [QR Studio](https://github.com/lovstudio/create-qrcode-skill) (`create-qrcode`) | Generate a scan-ready QR code using saved preferences; output only the code by default and add poster framing only when requested. — requires: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Dev Diary](https://github.com/lovstudio/skills) (`daily-post`) | Write a daily project update from real changes — requires: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Image Narrator](https://github.com/lovstudio/describe-image-skill) (`describe-image`) | Give text-only models sight — describe any image via a free vision model. |
| ![Free](https://img.shields.io/badge/Free-green) | [Fact Checker](https://github.com/lovstudio/fact-check-skill) (`fact-check`) | Verify claims like a careful researcher, with primary sources, counterexamples, confidence, and next steps. — related: `image-translation-errata` |
| ![Free](https://img.shields.io/badge/Free-green) | [Five-Unit Replies](https://github.com/lovstudio/skills) (`five`) | Use a five-unit concise reply mode — requires: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Hanzi Lens](https://github.com/lovstudio/hanzi-lens-skill) (`hanzi-lens`) | See one Chinese character through evidence — readings, form, history, classical context, meaning, and a professional visual. — requires: `professional-infographic` |
| ![Free](https://img.shields.io/badge/Free-green) | [Image Maker](https://github.com/lovstudio/image-creator-skill) (`image-creator`) | Create an image, designed graphic, or image prompt — requires: `branding-consistency`; related: `professional-infographic`, `professional-portrait`, `riso-portrait`, `image-translation-errata` |
| ![Free](https://img.shields.io/badge/Free-green) | [Image Translation Review](https://github.com/lovstudio/image-translation-errata-skill) (`image-translation-errata`) | Expose bad machine translation, show the correction, and preserve the original image. — related: `translation-review`, `image-creator`, `fact-check` |
| ![Free](https://img.shields.io/badge/Free-green) | [Knowledge Organizer](https://github.com/lovstudio/skills) (`kb-organize`) | Organize a knowledge base and its references — requires: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Media Downloader](https://github.com/lovstudio/media-crawler-skill) (`media-crawler`) | Turn an authorized social-media link into a verified local media file with resumable downloads and diagnostics. |
| ![Free](https://img.shields.io/badge/Free-green) | [Media Finder](https://github.com/lovstudio/media-fetch-skill) (`media-fetch`) | Find the right edition, resume through the faster transport, and verify the local media and subtitle status. |
| ![Free](https://img.shields.io/badge/Free-green) | [Knowledge Capture](https://github.com/lovstudio/skills) (`memory-add`) | Save a knowledge note with categories and tags — requires: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Knowledge Finder](https://github.com/lovstudio/skills) (`memory-search`) | Search a personal knowledge base — requires: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Image Prompt Crafter](https://github.com/lovstudio/skills) (`nano-banana-pro`) | Create a structured image prompt — requires: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Content Keeper](https://github.com/lovstudio/skills) (`output`) | Save the current content to a file — requires: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [WeChat Moments Copy](https://github.com/lovstudio/skills) (`output-wechat-moment`) | Format and save a WeChat Moments post — requires: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [My Vocabulary](https://github.com/lovstudio/personal-vocabulary-skill) (`personal-vocabulary`) | One personal vocabulary reused across speech-input apps. |
| ![Free](https://img.shields.io/badge/Free-green) | [A Little Encouragement](https://github.com/lovstudio/praise-before-work-skill) (`praise-before-work`) | Start each task with specific encouragement, then get to work. |
| ![Free](https://img.shields.io/badge/Free-green) | [WeChat Article Reader](https://github.com/MarkShawn2020/read-wechat-article-skill) (`read-wechat-article`) | Turn a public WeChat article URL into offline Markdown with original images and metadata. — requires: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [File Finder](https://github.com/lovstudio/search-file-skill) (`search-file`) | Recover files from past AI chats with conversation evidence, existence checks, and durable-copy ranking. |
| ![Free](https://img.shields.io/badge/Free-green) | [X Post Recovery](https://github.com/lovstudio/search-twitter-skill) (`search-twitter`) | Recover verbatim X/Twitter posts, screenshot evidence, and the gaps that still cannot be proven. |
| ![Paid](https://img.shields.io/badge/Paid-blueviolet) | [Subtitle Freedom](https://github.com/lovstudio/subtitle-freedom-skill) (`subtitle-freedom`) | Make learner subtitles that keep the selected level and harder expressions, with spoiler-safe ASS cards and optional no-burn watermark sidecars. |
| ![Free](https://img.shields.io/badge/Free-green) | [Deep Thinking](https://github.com/lovstudio/skills) (`think`) | Analyze a complex decision and its tradeoffs — requires: `branding-consistency` |
| ![Paid](https://img.shields.io/badge/Paid-blueviolet) | [Dictation Editor](https://github.com/lovstudio/typeless-prompt-skill) (`typeless-prompt`) | Turn rough dictation into concise, structured, send-ready text without answering or executing it. |
| ![Paid](https://img.shields.io/badge/Paid-blueviolet) | [Universal WeChat Key](https://github.com/lovstudio/wdb-cli-skill) (`wdb-cli`) | Prepare local WeChat keys, then read isolated database copies with exact record identity. — requires: `branding-consistency` |
| ![Paid](https://img.shields.io/badge/Paid-blueviolet) | [Weitan CLI](https://github.com/lovstudio/wxmp-cli-skill) (`wxmp-cli`) | Find cached WeChat articles and export them in four formats, with a complete CLI runtime included. — requires: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Xiaohongshu Researcher](https://github.com/lovstudio/xhs-skill) (`xhs`) | Research a Xiaohongshu topic and get a source-backed report, not just another search result. — requires: `branding-consistency` |
| **Business** | | |
| ![Free](https://img.shields.io/badge/Free-green) | [BP Studio](https://github.com/lovstudio/bp-skill) (`bp`) | A composable BP skill kit — use outline, deck, and polish alone or run the complete investor workflow. — requires: `bp-outline`, `bp-deck`, `bp-polish` |
| ![Free](https://img.shields.io/badge/Free-green) | [BP Master](https://github.com/lovstudio/bp-skill) (`bp-deck`) | Turn an approved BP outline into a professional PPTX, PDF, and full-deck preview with deliberate style selection. — requires: `any2deck` |
| ![Free](https://img.shields.io/badge/Free-green) | [BP Blueprint](https://github.com/lovstudio/bp-skill) (`bp-outline`) | Turn project evidence into an investor narrative and a source-backed 12–15 slide outline before making PPT. |
| ![Free](https://img.shields.io/badge/Free-green) | [BP Polish](https://github.com/lovstudio/bp-skill) (`bp-polish`) | Audit and polish an existing BP with a scored report and page-level fixes—without changing the facts. |
| ![Free](https://img.shields.io/badge/Free-green) | [Contract Reviewer](https://github.com/lovstudio/contract-review-pro-skill) (`contract-review-pro`) | Professional-grade contract review — four-layer methodology, structured comments with risk levels, summary, opinion, and business flowchart. |
| ![Paid](https://img.shields.io/badge/Paid-blueviolet) | [Event Planner](https://github.com/lovstudio/event-curator-skill) (`event-curator`) | Turn a guest bio into a ready-to-run event plan — title, rundown, host questions, and gifts. — related: `publish-event-onto-hdx` |
| ![Free](https://img.shields.io/badge/Free-green) | [Expense Assistant](https://github.com/lovstudio/expense-report-skill) (`expense-report`) | Turn a pile of invoices into a categorized Excel expense report. |
| ![Paid](https://img.shields.io/badge/Paid-blueviolet) | [Proposal Expert](https://github.com/lovstudio/proposal-skill) (`proposal`) | Turn a project brief into a complete, client-ready business proposal. |
| ![Free](https://img.shields.io/badge/Free-green) | [Huodongxing Diagnostics](https://github.com/lovstudio/publish-event-onto-hdx-skill) (`publish-event-onto-hdx`) | Find out why your Huodongxing event is missing from its category page, and what to change to get seen. — related: `event-curator`, `event-poster` |
| ![Free](https://img.shields.io/badge/Free-green) | [Contract Polish](https://github.com/lovstudio/review-doc-skill) (`review-doc`) | Review a document or contract and return it with inline comments. |
| ![Free](https://img.shields.io/badge/Free-green) | [Solution Architect](https://github.com/lovstudio/solution-architect-skill) (`solution-architect`) | Turn a product or technical requirement into a researched, open-source-first implementation plan. |
| **Design** | | |
| ![Free](https://img.shields.io/badge/Free-green) | [Business Card Studio](https://github.com/lovstudio/business-card-skill) (`business-card`) | Turn anyone's name, roles and tagline into a polished editorial business card — high-res PNG plus a click-to-download HTML. |
| ![Paid](https://img.shields.io/badge/Paid-blueviolet) | [Professional Poster](https://github.com/lovstudio/event-poster-skill) (`event-poster`) | Turn an event brief into a polished poster, ready to share or print for exhibitions. — related: `publish-event-onto-hdx` |
| ![Free](https://img.shields.io/badge/Free-green) | [Logo Radar](https://github.com/lovstudio/find-logo-skill) (`find-logo`) | Collect brand logos from public sources — wide and transparent preferred, archived for website/PPT/poster lineups. |
| ![Free](https://img.shields.io/badge/Free-green) | [Interface Designer](https://github.com/lovstudio/frontend-design-skill) (`frontend-design`) | Turn real content and existing code into distinctive, usable interfaces with verified interactions and media. — requires: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Partner Directory](https://github.com/lovstudio/maintain-partners-skill) (`maintain-partners`) | Scrape, normalize, and wire brand logos into the partners section across 4 locales in one shot. — requires: `find-logo` |
| ![Free](https://img.shields.io/badge/Free-green) | [Mobile Infographic](https://github.com/lovstudio/mobile-infographic-skill) (`mobile-infographic`) | Turn an existing conclusion into vertical infographics a phone can actually read, with type floors, safe areas, and an audit report. — requires: `branding-consistency`; related: `professional-infographic` |
| ![Paid](https://img.shields.io/badge/Paid-blueviolet) | [Website Whiz](https://github.com/lovstudio/oh-my-landingpage-skill) (`oh-my-landingpage`) | Turn product truth into a distinctive landing page, with brand, story, visual direction, implementation, and production review working as one system. |
| ![Paid](https://img.shields.io/badge/Paid-blueviolet) | [Professional Infographic](https://github.com/lovstudio/professional-infographic-skill) (`professional-infographic`) | Turn dense material or an investment path into one sourced visual argument, from entry and staged exits to the decision that follows. — related: `image-creator`, `mobile-infographic` |
| ![Free](https://img.shields.io/badge/Free-green) | [Professional Portrait](https://github.com/lovstudio/professional-portrait-skill) (`professional-portrait`) | Turn one photo into a clean, identity-preserving professional portrait. — related: `image-creator`, `riso-portrait` |
| ![Free](https://img.shields.io/badge/Free-green) | [Riso Portrait](https://github.com/lovstudio/riso-portrait-skill) (`riso-portrait`) | Turn one photo into a recognizable Riso avatar, then check the face, hands, objects, and circular crop. — related: `image-creator`, `professional-portrait` |
| ![Paid](https://img.shields.io/badge/Paid-blueviolet) | [Style Sampler](https://github.com/lovstudio/visual-clone-skill) (`visual-clone`) | Extract the design DNA of a reference image so you can recreate the look. |
| **Academic** | | |
| ![Paid](https://img.shields.io/badge/Paid-blueviolet) | [Academic Translator](https://github.com/lovstudio/academic-translator-skill) (`academic-translator`) | Translate English papers into Chinese while preserving figures, equations, pages, and navigation. |
| ![Paid](https://img.shields.io/badge/Paid-blueviolet) | [Paper Translator](https://github.com/lovstudio/paper-translator-skill) (`paper-translator`) | Translate academic PDFs into Chinese with matched pages, bilingual layouts, figures, and formulas. |
| ![Free](https://img.shields.io/badge/Free-green) | [Thesis Polish](https://github.com/lovstudio/thesis-polish-skill) (`thesis-polish`) | Polish an MBA thesis across language, structure, argument, and originality. |
| ![Free](https://img.shields.io/badge/Free-green) | [Translation Review](https://github.com/lovstudio/translation-review-skill) (`translation-review`) | Review a Chinese→English translation against the original across six quality dimensions. — related: `image-translation-errata` |
| **Office Automation** | | |
| ![Free](https://img.shields.io/badge/Free-green) | [PPT Master](https://github.com/lovstudio/any2deck-skill) (`any2deck`) | Turn any content into a styled slide deck — 16 looks, export to PPTX or PDF. — related: `any2pdf`, `any2docx` |
| ![Free](https://img.shields.io/badge/Free-green) | [Word Master](https://github.com/lovstudio/any2docx-skill) (`any2docx`) | Convert Markdown into a clean, professionally styled Word document. — related: `any2pdf`, `any2deck` |
| ![Free](https://img.shields.io/badge/Free-green) | [PDF Master](https://github.com/lovstudio/any2pdf-skill) (`any2pdf`) | Typeset Markdown into a publication-quality PDF with 16 themes, including Songti Reading. — related: `any2docx`, `any2deck` |
| ![Free](https://img.shields.io/badge/Free-green) | [Form Assistant](https://github.com/lovstudio/fill-form-skill) (`fill-form`) | Fill Word (.docx) form templates automatically, with clean CJK typography. |
| ![Free](https://img.shields.io/badge/Free-green) | [Web Form Assistant](https://github.com/lovstudio/fill-web-form-skill) (`fill-web-form`) | Answer online forms using your own knowledge base as the source of truth. |
| ![Free](https://img.shields.io/badge/Free-green) | [PDF Scroll](https://github.com/lovstudio/pdf2png-skill) (`pdf2png`) | Convert a PDF to a single long PNG — fast enough to feel instant on macOS. |
| ![Free](https://img.shields.io/badge/Free-green) | [Vector Tracer](https://github.com/lovstudio/png2svg-skill) (`png2svg`) | Convert a PNG to a crisp SVG, with background removed and curves smoothed. |
| ![Free](https://img.shields.io/badge/Free-green) | [Rich Export](https://github.com/lovstudio/rich-export-skill) (`rich-export`) | Export one rich-media source into web, editable document, print, and archive formats. |
| ![Free](https://img.shields.io/badge/Free-green) | [Yoda Automation](https://github.com/lovstudio/yoda-automation-skill) (`yoda-automation`) | Create reliable Yoda reminders and recurring follow-ups with verified schedules, run evidence, and a precise stop rule. |
| **Content Creation** | | |
| ![Free](https://img.shields.io/badge/Free-green) | [WeChat Writer](https://github.com/lovstudio/article-creator-skill) (`article-creator`) | Create, rewrite, brand, or faithfully repost a complete WeChat article package before publication. — requires: `branding-consistency`, `writing-style` |
| ![Free](https://img.shields.io/badge/Free-green) | [Brand Editor](https://github.com/lovstudio/branding-consistency-skill) (`branding-consistency`) | Keep visible copy aligned with its audience, brand role, component, and real publishing context. |
| ![Free](https://img.shields.io/badge/Free-green) | [Deep Research](https://github.com/lovstudio/deep-research-skill) (`deep-research`) | Produce citation-tracked research reports with persistent evidence, claim verification, and shareable open-source solution catalogs. |
| ![Free](https://img.shields.io/badge/Free-green) | [Document Illustrator](https://github.com/lovstudio/document-illustrator-skill) (`document-illustrator`) | Illustrate a long document in place — plan, generate, and insert images automatically. — requires: `image-creator` |
| ![Free](https://img.shields.io/badge/Free-green) | [Text Editor](https://github.com/lovstudio/human-writing-skill) (`human-writing`) | Preserve the author's real judgments, repair discourse problems, then measure and retest surface patterns. — requires: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [WeChat Publisher](https://github.com/lovstudio/publish-wechat-article-skill) (`publish-wechat-article`) | Move a prepared article through WeChat draft creation, persisted-state verification, and publication without confusing a saved draft with a live post. — requires: `env-management`, `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Voice Replica](https://github.com/lovstudio/style-clone-skill) (`style-clone`) | Extract a writing style profile from sample articles, then rewrite any content in that style. |
| ![Paid](https://img.shields.io/badge/Paid-blueviolet) | [Book Writing Expert](https://github.com/lovstudio/write-professional-book-skill) (`write-professional-book`) | Write a full multi-chapter book — technical, tutorial, or monograph — from an outline. |
| ![Free](https://img.shields.io/badge/Free-green) | [My Writing Voice](https://github.com/lovstudio/writing-style-skill) (`writing-style`) | Write from verified facts in a calibrated personal voice, then pass authorship, discourse, surface, audience, and brand gates. — requires: `branding-consistency`, `human-writing` |
| ![Paid](https://img.shields.io/badge/Paid-blueviolet) | [WeChat Archiver](https://github.com/lovstudio/wxmp-cracker-skill) (`wxmp-cracker`) | Archive WeChat Official Account articles into clean, reusable text. |
| **Dev Tools** | | |
| ![Free](https://img.shields.io/badge/Free-green) | [Task Capture](https://github.com/lovstudio/skills) (`add-task`) | Add an item to the current task list — requires: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Web Tool Studio](https://github.com/lovstudio/skills) (`add-tool`) | Add an online tool to an existing website — requires: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Agent Guide Keeper](https://github.com/lovstudio/skills) (`agent-instructions`) | Review or improve project agent instructions — requires: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [App Studio](https://github.com/lovstudio/app-generator-skill) (`app-generator`) | Generate Lovstudio-grade web, PWA, or Tauri apps with brand, UI, data, deploy/release, and developer tooling wired in. |
| ![Free](https://img.shields.io/badge/Free-green) | [Architecture Atlas](https://github.com/lovstudio/skills) (`architecture-documentation`) | Create architecture documentation from a codebase — requires: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Ataru Indexing](https://github.com/lovstudio/ataru-indexing-skill) (`ataru-indexing`) | Make sure your local AI session memory is actually searchable before you search it. |
| ![Free](https://img.shields.io/badge/Free-green) | [Context Sentinel](https://github.com/lovstudio/auto-context-skill) (`auto-context`) | Watch your Claude Code context for pollution and suggest when to fork or reset. |
| ![Free](https://img.shields.io/badge/Free-green) | [CSS Polish](https://github.com/lovstudio/skills) (`better-css`) | Refactor CSS and Tailwind styles — requires: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [GitHub Repository Description Optimization](https://github.com/lovstudio/skills) (`better-github-desc`) | Update a GitHub repository description from its README — requires: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Project Organizer](https://github.com/lovstudio/skills) (`better-project-structure`) | Improve a project directory structure — requires: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [README Polish](https://github.com/lovstudio/skills) (`better-readme`) | Create or improve a project README — requires: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Next.js SEO Assistant](https://github.com/lovstudio/skills) (`better-seo`) | Review and improve Next.js SEO — requires: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Status Line Studio](https://github.com/lovstudio/skills) (`better-statusline`) | Update an agent status line with rollback — requires: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Session Mover](https://github.com/lovstudio/cc-migrate-session) (`cc-migrate-session`) | Keep your Claude Code session history working after you move a project folder. |
| ![Free](https://img.shields.io/badge/Free-green) | [Check Balance](https://github.com/lovstudio/check-balance-skill) (`check-balance`) | See how much quota your accounts across multiple platforms (cc, codex, ds and more) have left, and when each limit resets. |
| ![Free](https://img.shields.io/badge/Free-green) | [Project Checkpoint](https://github.com/lovstudio/skills) (`checkpoint`) | Create a project checkpoint — requires: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Checkpoint History](https://github.com/lovstudio/skills) (`checkpoint-list`) | List a project checkpoint history — requires: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Clash Network Doctor](https://github.com/lovstudio/clash-tun-doctor-skill) (`clash-tun-doctor`) | Diagnose Clash TUN failures from runtime evidence, apply reversible fixes, and verify the real application path. — related: `env-management` |
| ![Free](https://img.shields.io/badge/Free-green) | [API Studio](https://github.com/lovstudio/cli2anything-skill) (`cli2anything`) | Turn authorized observed APIs into verified contracts, SDKs, Swagger, and task-focused CLIs. |
| ![Free](https://img.shields.io/badge/Free-green) | [Project Makeover](https://github.com/lovstudio/skills) (`clone-rebrand`) | Create a project from a template and rebrand it — requires: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Code Reviewer](https://github.com/lovstudio/skills) (`code-review`) | Review a code change for actionable defects — requires: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Vercel Deployer](https://github.com/lovstudio/deploy-to-vercel-skill) (`deploy-to-vercel`) | Ship a frontend to Vercel with custom domain and Cloudflare DNS wired up automatically. |
| ![Free](https://img.shields.io/badge/Free-green) | [Tech Selection Advisor](https://github.com/lovstudio/skills) (`dev-research`) | Research a development plan and technology choices — requires: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Lesson Distiller](https://github.com/lovstudio/skills) (`distill`) | Distill a solved problem into reusable knowledge — requires: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Lessons to Rules](https://github.com/lovstudio/skills) (`distill-to-system`) | Persist a reusable lesson in agent instructions — requires: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [DSH Plugin Studio](https://github.com/lovstudio/dsh-plugin-creator-skill) (`dsh-plugin-creator`) | Author a DSH plugin end-to-end — pick the extension point, scaffold, implement, and pass the repo gates. — related: `dsh-plugin-publisher` |
| ![Free](https://img.shields.io/badge/Free-green) | [DSH Plugin Publisher](https://github.com/lovstudio/dsh-plugin-publisher-skill) (`dsh-plugin-publisher`) | Publish a validated DSH plugin across npm, git, and tarball channels with per-channel load evidence. — related: `dsh-plugin-creator` |
| ![Free](https://img.shields.io/badge/Free-green) | [Desktop App Relaunch](https://github.com/lovstudio/electron-app-relaunch-skill) (`electron-app-relaunch`) | Add a real Electron relaunch while keeping renderer reload and update handoff separate. |
| ![Free](https://img.shields.io/badge/Free-green) | [Electron Delta Updates](https://github.com/lovstudio/electron-delta-updater-skill) (`electron-delta-updater`) | Build verified Electron delta updates with Sparkle, appcasts, signing, and installation proof. |
| ![Free](https://img.shields.io/badge/Free-green) | [Credential Keeper](https://github.com/lovstudio/env-management-skill) (`env-management`) | Track every account and rotating Key, select one binding per environment target, and keep secrets off the Dashboard. — related: `install-ai`, `clash-tun-doctor` |
| ![Free](https://img.shields.io/badge/Free-green) | [Finder Actions](https://github.com/lovstudio/finder-action-skill) (`finder-action`) | Create a Finder context menu action — requires: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Link Fixer](https://github.com/lovstudio/skills) (`fix-broken-links`) | Find and fix broken links in a project — requires: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Log Detective](https://github.com/lovstudio/skills) (`fix-by-add-log`) | Debug a problem with targeted logging — requires: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Session Rescuer](https://github.com/lovstudio/fix-codex-session-skill) (`fix-codex-session`) | Diagnose a Codex thread stuck on a tool-call error or a stale provider binding, recover the deliverables it left on disk, and get a path you can continue. |
| ![Free](https://img.shields.io/badge/Free-green) | [Troubleshooter](https://github.com/lovstudio/skills) (`fix-general`) | Diagnose and fix a software error — requires: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Verified Fixes](https://github.com/lovstudio/skills) (`fix-until-no-error`) | Fix errors until the specified checks pass — requires: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Logo Studio](https://github.com/lovstudio/skills) (`gen-logo`) | Create a logo and application icon — requires: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Project Namer](https://github.com/lovstudio/skills) (`gen-project-name`) | Generate a project name from its purpose — requires: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [GitHub Collaborator Manager](https://github.com/lovstudio/gh-access-skill) (`gh-access`) | Grant, revoke, or audit collaborator access on private GitHub repos in one command. |
| ![Free](https://img.shields.io/badge/Free-green) | [Open Source Contributor](https://github.com/lovstudio/gh-contribute-skill) (`gh-contribute`) | Ship a clean PR to any upstream GitHub repo — fork, branch, push, and open PR for you. |
| ![Free](https://img.shields.io/badge/Free-green) | [GitHub Organizer](https://github.com/lovstudio/gh-tidy-skill) (`gh-tidy`) | Triage and clean up GitHub issues, PRs, branches, and labels in a single pass. |
| ![Free](https://img.shields.io/badge/Free-green) | [Context Commit](https://github.com/lovstudio/skills) (`git-commit-with-context`) | Create a Git commit for the current task changes — requires: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Command Helper](https://github.com/lovstudio/skills) (`help-cmd`) | Create a command line for a task — requires: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [I18n Inspector](https://github.com/lovstudio/skills) (`i18n-check-i18n`) | Review and fix frontend internationalization — requires: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Document Visuals](https://github.com/lovstudio/skills) (`illustrate`) | Illustrate a document with evidence and relevant images — requires: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Supabase Auth Setup](https://github.com/lovstudio/skills) (`init-auth`) | Add Supabase authentication to a React application — requires: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Port Setup](https://github.com/lovstudio/skills) (`init-port`) | Configure a stable development port — requires: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [AI Integrator](https://github.com/lovstudio/install-ai-skill) (`install-ai`) | Add an App AI feature with Agent Client, MaaS routing, model intent, and optional UI. — related: `env-management` |
| ![Free](https://img.shields.io/badge/Free-green) | [Design System Setup](https://github.com/lovstudio/skills) (`install-design`) | Install a project design system — requires: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [shadcn/ui Setup](https://github.com/lovstudio/skills) (`install-shadcn-ui`) | Install and configure shadcn/ui for a project — requires: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [TanStack Query Setup](https://github.com/lovstudio/install-tanstack-query-skill) (`install-tanstack-query`) | Initialize TanStack Query and migrate request state into shared query keys and hooks. |
| ![Free](https://img.shields.io/badge/Free-green) | [Tauri Icon Setup](https://github.com/lovstudio/skills) (`install-tauri-logo`) | Install a logo in a Tauri application — requires: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Website Logo Setup](https://github.com/lovstudio/skills) (`install-web-logo`) | Install a web logo and favicon set — requires: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [ZenMux Setup](https://github.com/lovstudio/skills) (`install-zenmux-api`) | Integrate the ZenMux API through a secure backend — requires: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Lovinsp Setup](https://github.com/lovstudio/integrate-lovinsp-skill) (`integrate-lovinsp`) | Integrate Lovinsp in a frontend project, including plain JS Vite DOM annotation — requires: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Emoji Makeover](https://github.com/lovstudio/skills) (`kill-emoji`) | Replace interface emoji with appropriate icons — requires: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Website Legal Pages](https://github.com/lovstudio/skills) (`legal-pages`) | Draft website privacy and terms pages — requires: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Workflow Studio](https://github.com/lovstudio/skills) (`meta-command`) | Turn a repeated command workflow into a portable skill — requires: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Mobile Fit](https://github.com/lovstudio/mobile-adapt-skill) (`mobile-adapt`) | Scan a web project for mobile issues and fix them — overflow, safe area, viewport units, responsive layouts, and page navigation. |
| ![Free](https://img.shields.io/badge/Free-green) | [npm Publisher](https://github.com/lovstudio/lov-npm-publisher-skill) (`npm-publisher`) | Publish npm packages without repeated login — OIDC trusted publishing or a local NPM_TOKEN. |
| ![Free](https://img.shields.io/badge/Free-green) | [Obsidian Dev Sync](https://github.com/lovstudio/skills) (`obsidian-ensure-dev-sync`) | Fix an Obsidian plugin development sync chain — requires: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Obsidian Cache Reset](https://github.com/lovstudio/obsidian-reset-cache-skill) (`obsidian-reset-cache`) | Reset Obsidian's cache when it gets stuck on "Loading cache". |
| ![Free](https://img.shields.io/badge/Free-green) | [Codex Task Launcher](https://github.com/lovstudio/open-codex-session-skill) (`open-codex-session`) | Open the exact Codex task you mean, then verify the desktop actually navigated. |
| ![Free](https://img.shields.io/badge/Free-green) | [Tauri Backend Tuner](https://github.com/lovstudio/optimize-tauri-backend-skill) (`optimize-tauri-backend`) | Reduce Tauri Rust restart pain by modularizing the backend, shrinking command surfaces, and hardening long IPC streams. |
| ![Free](https://img.shields.io/badge/Free-green) | [Storage Organizer](https://github.com/lovstudio/organize-storage-skill) (`organize-storage`) | Turn a messy drive into a project-first archive without deleting or overwriting. — requires: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Port Keeper](https://github.com/lovstudio/project-port-skill) (`project-port`) | Assign each project a stable, unique dev port so services stop colliding. |
| ![Free](https://img.shields.io/badge/Free-green) | [API Refiner](https://github.com/lovstudio/skills) (`refactor-api`) | Refactor redundant backend APIs — requires: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Module Refactorer](https://github.com/lovstudio/skills) (`refactor-modular`) | Refactor a large file into cohesive modules — requires: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Release Pilot](https://github.com/lovstudio/release-via-cicd-skill) (`release-via-cicd`) | Set up or run a verified CI/CD release — requires: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Project Renamer](https://github.com/lovstudio/skills) (`rename-project`) | Rename a project and preserve compatibility — requires: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Repository Takeover](https://github.com/lovstudio/skills) (`repo-takeover`) | Publish a cloned repository under your account — requires: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Docs Site Builder](https://github.com/lovstudio/repo2docs-skill) (`repo2docs`) | Turn any folder — code, articles, images — into a polished Fumadocs site, built incrementally and shipped to {id}.lovstudio.ai/docs. |
| ![Free](https://img.shields.io/badge/Free-green) | [Chat Finder](https://github.com/lovstudio/search-chat-skill) (`search-chat`) | Find what you and your AI already worked out, and read it back in its original context. |
| ![Free](https://img.shields.io/badge/Free-green) | [Skill Alchemist](https://github.com/lovstudio/skill-distiller-skill) (`skill-distiller`) | Turn delivery history into a clear, reusable Skill blueprint with boundaries and acceptance checks. |
| ![Free](https://img.shields.io/badge/Free-green) | [Skill Pricer](https://github.com/lovstudio/skill-pricing-skill) (`skill-pricing`) | Turn Skill pricing into an explainable decision backed by cost, value, confidence, and channel fit. |
| ![Free](https://img.shields.io/badge/Free-green) | [Skill Publisher](https://github.com/lovstudio/skill-publisher-skill) (`skill-publisher`) | Auto-price every release, publish to the LovStudio website by default, and expand only to explicitly requested channels. — requires: `skill-pricing` |
| ![Free](https://img.shields.io/badge/Free-green) | [Synology Sync](https://github.com/lovstudio/sync-with-synology-skill) (`sync-with-synology`) | Move local files to Synology with verified uploads and safe local pruning. |
| ![Free](https://img.shields.io/badge/Free-green) | [Version Keeper](https://github.com/lovstudio/skills) (`version-management`) | Manage package versions with Changesets — requires: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Version Review](https://github.com/lovstudio/skills) (`version-management-manual`) | Create a changeset for manual review — requires: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [XBTI Gallery](https://github.com/lovstudio/xbti-gallery-skill) (`xbti-gallery`) | Browse a gallery of XBTI personality tests — requires: `branding-consistency` |
| **Video Creation** | | |
| ![Paid](https://img.shields.io/badge/Paid-blueviolet) | [Video Studio](https://github.com/lovstudio/media-creator-skill) (`media-creator`) | Turn recordings and Screen Studio projects into reviewable video, then deliver approved horizontal and vertical videos, covers, and quality reports. — requires: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Video Prep](https://github.com/lovstudio/media-preprocessor-skill) (`media-preprocessor`) | Enhance long recordings and organize useful segments with verified source timecodes. — requires: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Video Publisher](https://github.com/lovstudio/media-publisher-skill) (`media-publisher`) | Preserve the user's final copy while publishing to WeChat Channels or Bilibili with cover, confirmation, and status gates. — requires: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Camera Media Keeper](https://github.com/lovstudio/migrate-camera-media-skill) (`migrate-camera-media`) | Transfer camera media to SSD, verify every file, and keep an auditable copy report. — requires: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [WeChat Channels Publisher](https://github.com/lovstudio/publish-wechat-channels-skill) (`publish-wechat-channels`) | Publish WeChat Channels videos with preflight, field readback, and status verification. |
| ![Free](https://img.shields.io/badge/Free-green) | [Video Chapters](https://github.com/lovstudio/video-chapter-skill) (`video-chapter`) | Plan chapters, tune the progress bar in React Studio, then export an overlay, final video, or editor package. |
| ![Free](https://img.shields.io/badge/Free-green) | [Video Stills](https://github.com/lovstudio/video-moments-skill) (`video-moments`) | Select real moments from event videos, restore color, and deliver consistently bright photos with source timecodes. — requires: `branding-consistency` |
| **Meta** | | |
| ![Free](https://img.shields.io/badge/Free-green) | [Skill Showcase](https://github.com/lovstudio/skill-add-case-skill) (`skill-add-case`) | Share an accepted Skill result through your LovStudio account, manually or with an Agent. — requires: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Skill Studio](https://github.com/lovstudio/skill-creator-skill) (`skill-creator`) | Create, migrate, validate and install portable Agent Skills — requires: `branding-consistency` |
| ![Free](https://img.shields.io/badge/Free-green) | [Skill Refiner](https://github.com/lovstudio/skill-optimizer-skill) (`skill-optimizer`) | Audit an existing skill, auto-fix issues, and bump its version in one pass. |
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
