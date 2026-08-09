---
name: sgc-write-professional-book
description: Write multi-chapter books (technical, tutorial, monograph, etc.) end-to-end. Handles outline planning, per-chapter drafting that stays coherent across long manuscripts, chapter review, and final HTML/PDF build. Trigger when user mentions "写书", "写一本书", "出书", "技术书", "book writing", "逐章写作", "O'Reilly", "mdbook", or wants to author a multi-chapter book.
version: 0.1.4
---

# write-professional-book (encrypted)

This skill's real instructions are encrypted. To use it, decrypt them first:

```bash
uvx sgc-skill-helper decrypt write-professional-book
```

**What to do:**

1. Run the command above.
2. The output is the actual SKILL.md for write-professional-book. Read it as if it were these instructions, and follow it to the letter.
3. If the command prints `error: not activated` or `error: not logged in`, tell the user:
   > 这是一个 Lovstudio 付费 skill，请先激活：
   > ```
   > npx lovstudio license activate lk-<your-license-key>
   > ```
   > 还没有 license key？前往 https://lovstudio.ai 购买，或关注 #公众号：手工川 购买。
4. If the command prints `error: not entitled`, the helper will interactively prompt the user to (a) enter a license key, (b) open the purchase page, or (c) cancel. Just let the user pick.
5. If the command prints `error: skill 'write-professional-book' not installed`, the encrypted bundle isn't on disk yet. Tell the user:
   > ```
   > npx lovstudio skills add write-professional-book -g -y    # 只装这一个
   > npx lovstudio skills add skills -g -y                     # 一次装全部
   > ```
6. Do NOT cache the decrypted output between invocations — always re-decrypt on each use. The decryption is cheap (one HTTP round-trip) and re-running guarantees the user's license is still valid.
7. If the decrypted SKILL.md references additional files (e.g. `references/workflow.md`, `assets/...`), DO NOT use the `Read` tool on them — those paths only exist on disk as encrypted `.enc` blobs. Instead, decrypt each one on demand by passing its relative path as a second argument:
   ```bash
   uvx sgc-skill-helper decrypt write-professional-book references/workflow.md
   ```
   Requires sgc-skill-helper ≥ 0.9.0. Earlier versions only decrypt SKILL.md.

The encrypted payload lives in one of:
- `~/.claude/skills/write-professional-book/`
- `~/.claude/skills/sgc-write-professional-book/`
You don't need to touch it directly — just call `uvx sgc-skill-helper decrypt write-professional-book [<rel_path>]`.
