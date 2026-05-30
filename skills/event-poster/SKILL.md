---
name: lovstudio-event-poster
description: 'Create event posters, exhibition posters, flyers, and promotional graphics from a brief. Outputs print-ready high-resolution PNG. Trigger words: 海报, poster, event poster, 展览海报, 展架, 活动海报, 宣传图, promotional, banner, flyer'
version: 0.4.0
---

# event-poster (encrypted)

This skill's real instructions are encrypted. To use it, decrypt them first:

```bash
uvx lovstudio-skill-helper decrypt event-poster
```

**What to do:**

1. Run the command above.
2. The output is the actual SKILL.md for event-poster. Read it as if it were these instructions, and follow it to the letter.
3. If the command prints `error: not activated` or `error: not logged in`, tell the user:
   > 这是一个 Lovstudio 付费 skill，请先激活：
   > ```
   > npx lovstudio license activate lk-<your-license-key>
   > ```
   > 还没有 license key？前往 https://lovstudio.ai 购买，或关注 #公众号：手工川 购买。
4. If the command prints `error: not entitled`, the helper will interactively prompt the user to (a) enter a license key, (b) open the purchase page, or (c) cancel. Just let the user pick.
5. If the command prints `error: skill 'event-poster' not installed`, the encrypted bundle isn't on disk yet. Tell the user:
   > ```
   > npx lovstudio skills add event-poster -g -y      # 只装这一个
   > npx lovstudio skills add skills -g -y            # 一次装全部
   > ```
6. Do NOT cache the decrypted output between invocations — always re-decrypt on each use. The decryption is cheap (one HTTP round-trip) and re-running guarantees the user's license is still valid.

The encrypted payload lives in one of:
- `~/.claude/skills/event-poster/`
- `~/.claude/skills/lovstudio-event-poster/`
You don't need to touch it directly — just call `uvx lovstudio-skill-helper decrypt event-poster`.
