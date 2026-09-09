---
name: lovstudio:wdb-cli
description: 万能微信秘钥：先为本地微信准备密钥，再查询聊天、联系人、朋友圈和任意只读 SQL。Use when the user mentions“万能微信秘钥”“查微信记录”“读取朋友圈”。
version: 0.4.0
---

# 万能微信秘钥 · Universal WeChat Key

This skill's real instructions are encrypted. To use it, decrypt them first:

```bash
uvx lovstudio-skill-helper decrypt wdb-cli
```

**What to do:**

1. Run the command above.
2. The output is the actual SKILL.md for wdb-cli. Read it as if it were these instructions, and follow it to the letter.
3. If the command prints `error: not activated` or `error: not logged in`, tell the user:
   > 这是一个 Lovstudio 付费 skill，请先激活（CLI 会打开浏览器让你登录，然后绑定你的 license key）：
   > ```
   > npx lovstudio license <your-license-key>
   > ```
   > 还没有 license key？前往 https://lovstudio.ai 购买，或关注 #公众号：手工川 购买。
4. If the command prints `error: not entitled`, the helper will interactively prompt the user to (a) enter a license key, (b) open the purchase page, or (c) cancel. Just let the user pick.
5. If the command prints `error: skill 'wdb-cli' not installed`, the encrypted bundle isn't on disk yet. Tell the user:
   > ```
   > npx lovstudio skills add wdb-cli                      # recommended: also checks deps
   > npx skills add lovstudio/skills --skill wdb-cli       # raw alternative
   > ```
6. Do NOT cache the decrypted output between invocations — always re-decrypt on each use. The decryption is cheap (one HTTP round-trip) and re-running guarantees the user's license is still valid.
7. If the decrypted SKILL.md references additional files (e.g. `references/workflow.md`, `assets/...`), DO NOT use the `Read` tool on them — those paths only exist on disk as encrypted `.enc` blobs. Instead, decrypt each one on demand by passing its relative path as a second argument:
   ```bash
   uvx lovstudio-skill-helper decrypt wdb-cli references/workflow.md
   ```
   Requires lovstudio-skill-helper ≥ 0.9.0. Earlier versions only decrypt SKILL.md.

The encrypted payload lives in one of:
- `~/.claude/skills/wdb-cli/`
- `~/.claude/skills/lovstudio-wdb-cli/`
You don't need to touch it directly — just call `uvx lovstudio-skill-helper decrypt wdb-cli [<rel_path>]`.
