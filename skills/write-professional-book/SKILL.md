---
name: write-professional-book
description: Write multi-chapter books using a GitHub repo as the single source of truth. Solves LLM context window limitations through a compressed book summary strategy (OUTLINE + BOOK_SUMMARY ≈ 9KB overhead). 5-phase workflow: Plan → Research → Write → Review → Build. Supports multiple styles: O'Reilly practical, academic monograph, tutorial series, etc. Outputs mdBook HTML (GitHub Pages) and pandoc PDF (CJK-ready). Trigger when user mentions "写书", "写一本书", "book writing", "出书", "技术书", "O'Reilly", "mdbook", "逐章写作", or wants to create a multi-chapter book.
version: 0.1.0
---

# write-professional-book (encrypted)

This skill's real instructions are encrypted. To use it, decrypt them first:

```bash
lovstudio-activate decrypt write-professional-book
```

**What to do:**

1. Run the command above.
2. The output is the actual SKILL.md for write-professional-book. Read it as if it were these instructions, and follow it to the letter.
3. If the command prints `error: not activated`, tell the user:
   > This is a paid Lovstudio skill. You need to activate it first:
   > ```
   > lovstudio-activate activate <your-license-key>
   > ```
   > If you don't have a license key, follow the 手工川 (ShougongChuan) WeChat official account to purchase one.
4. If the command prints `error: skill 'write-professional-book' not installed`, it means `~/.lovstudio/brand_skills/write-professional-book/` is empty. Tell the user to re-run `npx skills add lovstudio/skills` or to install the `lovstudio-activate` CLI (`pipx install lovstudio-activate`).
5. Do NOT cache the decrypted output between invocations — always re-decrypt on each use. The decryption is cheap (one HTTP round-trip) and re-running guarantees the user's license is still valid.

The encrypted payload lives in `~/.lovstudio/brand_skills/write-professional-book/` (or alongside this file, whichever the CLI finds). You don't need to touch it directly — just call `lovstudio-activate decrypt write-professional-book`.
