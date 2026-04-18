---
name: event-poster
description: Create event posters and promotional graphics. Generates a single-file plain HTML/CSS page (no JS framework dependencies), then renders to PNG via Playwright. The HTML is mobile-first (max-width 480px) so it previews correctly in browsers and renders cleanly at high DPI via the headless renderer. Trigger words: 海报, poster, event poster, 活动海报, 宣传图, promotional, banner, flyer
version: 0.3.0
---

# event-poster (encrypted)

This skill's real instructions are encrypted. To use it, decrypt them first:

```bash
lovstudio-activate decrypt event-poster
```

**What to do:**

1. Run the command above.
2. The output is the actual SKILL.md for event-poster. Read it as if it were these instructions, and follow it to the letter.
3. If the command prints `error: not activated`, tell the user:
   > This is a paid Lovstudio skill. You need to activate it first:
   > ```
   > lovstudio-activate activate <your-license-key>
   > ```
   > If you don't have a license key, follow the 手工川 (ShougongChuan) WeChat official account to purchase one.
4. If the command prints `error: skill 'event-poster' not installed`, it means `~/.lovstudio/brand_skills/event-poster/` is empty. Tell the user to re-run `npx skills add lovstudio/skills` or to install the `lovstudio-activate` CLI (`pipx install lovstudio-activate`).
5. Do NOT cache the decrypted output between invocations — always re-decrypt on each use. The decryption is cheap (one HTTP round-trip) and re-running guarantees the user's license is still valid.

The encrypted payload lives in `~/.lovstudio/brand_skills/event-poster/` (or alongside this file, whichever the CLI finds). You don't need to touch it directly — just call `lovstudio-activate decrypt event-poster`.
