---
name: lov-xhs
description: Default a Xiaohongshu topic request to a source-backed research report; use search-only mode only when requested. Use when the user mentions 小红书调研、攻略规划、选题研究、小红书搜索, or "search Xiaohongshu notes".
version: 0.2.0
---

# 小红书调研助手 · Xiaohongshu Researcher

This skill's real instructions are encrypted. To use it, decrypt them first:

```bash
uvx lovstudio-skill-helper decrypt xhs
```

**What to do:**

1. Run the command above.
2. The output is the actual SKILL.md for xhs. Read it as if it were these instructions, and follow it to the letter.
3. If the command prints `error: not activated` or `error: not logged in`, tell the user:
   > 这是一个 Lovstudio 付费 skill，请先激活（CLI 会打开浏览器让你登录，然后绑定你的 license key）：
   > ```
   > npx lovstudio license <your-license-key>
   > ```
   > 还没有 license key？前往 https://lovstudio.ai 购买，或关注 #公众号：手工川 购买。
4. If the command prints `error: not entitled`, the helper will interactively prompt the user to (a) enter a license key, (b) open the purchase page, or (c) cancel. Just let the user pick.
5. If the command prints `error: skill 'xhs' not installed`, the encrypted bundle isn't on disk yet. Tell the user:
   > ```
   > npx lovstudio skills add xhs                      # recommended: also checks deps
   > npx skills add lovstudio/skills --skill xhs       # raw alternative
   > ```
6. Do NOT cache the decrypted output between invocations — always re-decrypt on each use. The decryption is cheap (one HTTP round-trip) and re-running guarantees the user's license is still valid.
7. If the decrypted SKILL.md references additional files (e.g. `references/workflow.md`, `assets/...`), DO NOT use the `Read` tool on them — those paths only exist on disk as encrypted `.enc` blobs. Instead, decrypt each one on demand by passing its relative path as a second argument:
   ```bash
   uvx lovstudio-skill-helper decrypt xhs references/workflow.md
   ```
   Requires lovstudio-skill-helper ≥ 0.9.0. Earlier versions only decrypt SKILL.md.

The encrypted payload lives in one of:
- `~/.claude/skills/xhs/`
- `~/.claude/skills/lovstudio-xhs/`
You don't need to touch it directly — just call `uvx lovstudio-skill-helper decrypt xhs [<rel_path>]`.
