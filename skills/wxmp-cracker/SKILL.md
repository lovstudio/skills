---
name: sgc-wxmp-cracker
description: 微信公众号文章抓取与导出。自动处理 mp.weixin.qq.com 的登录态获取与续期， 支持按公众号搜索、抓取文章列表与正文、按日期窗口导出 Markdown / JSON / CSV。 Trigger when the user wants to crawl a WeChat public account, export recent articles, or 提到 "wcx"、"微信公众号"、"公众号文章"、"mp.weixin"、"抓公众号"、 "crawl wechat official account"、"wxmp"、"最近十天的文章"。
version: 0.1.6
dependencies:
- name: wcx
  check: wcx --help >/dev/null 2>&1
  install: pip install git+https://github.com/lovstudio/wcx.git
- name: agent-browser
  check: command -v agent-browser >/dev/null 2>&1
  install: npm i -g agent-browser
---

# wxmp-cracker (encrypted)

This skill's real instructions are encrypted. To use it, decrypt them first:

```bash
uvx sgc-skill-helper decrypt wxmp-cracker
```

**What to do:**

1. Run the command above.
2. The output is the actual SKILL.md for wxmp-cracker. Read it as if it were these instructions, and follow it to the letter.
3. If the command prints `error: not activated` or `error: not logged in`, tell the user:
   > 这是一个 Lovstudio 付费 skill，请先激活：
   > ```
   > npx lovstudio license activate lk-<your-license-key>
   > ```
   > 还没有 license key？前往 https://lovstudio.ai 购买，或关注 #公众号：手工川 购买。
4. If the command prints `error: not entitled`, the helper will interactively prompt the user to (a) enter a license key, (b) open the purchase page, or (c) cancel. Just let the user pick.
5. If the command prints `error: skill 'wxmp-cracker' not installed`, the encrypted bundle isn't on disk yet. Tell the user:
   > ```
   > npx lovstudio skills add wxmp-cracker -g -y      # 只装这一个
   > npx lovstudio skills add skills -g -y            # 一次装全部
   > ```
6. Do NOT cache the decrypted output between invocations — always re-decrypt on each use. The decryption is cheap (one HTTP round-trip) and re-running guarantees the user's license is still valid.
7. If the decrypted SKILL.md references additional files (e.g. `references/workflow.md`, `assets/...`), DO NOT use the `Read` tool on them — those paths only exist on disk as encrypted `.enc` blobs. Instead, decrypt each one on demand by passing its relative path as a second argument:
   ```bash
   uvx sgc-skill-helper decrypt wxmp-cracker references/workflow.md
   ```
   Requires sgc-skill-helper ≥ 0.9.0. Earlier versions only decrypt SKILL.md.

The encrypted payload lives in one of:
- `~/.claude/skills/wxmp-cracker/`
- `~/.claude/skills/sgc-wxmp-cracker/`
You don't need to touch it directly — just call `uvx sgc-skill-helper decrypt wxmp-cracker [<rel_path>]`.
