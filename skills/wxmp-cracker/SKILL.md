---
name: wxmp-cracker
description: 微信公众号文章抓取。自动获取 mp.weixin.qq.com 后台 token + cookie（通过 agent-browser 弹出 Chrome 扫码，持久化 profile 下次免扫），并调度 wcx CLI 完成 search / fetch / list / export 全流程。凭证失效时自动重新扫码并重试， 用户无需关心 token 维护。支持按日期窗口导出（`--since 10d|2w|2026-04-08`）、 同时输出 md + json + csv 三种索引。 Use when the user wants to crawl a WeChat public account, export recent articles, or fix an expired wcx login. 触发场景：用户想抓取某公众号的文章列表、按关键词搜公众号、下载文章正文、 按最近 N 天/周导出、导出 Markdown/JSON/CSV、分析某个号的内容；或提到 "wcx"、"微信公众号"、"公众号文章"、"mp.weixin"、"抓公众号"、 "crawl wechat official account"、"wxmp"、"登录失效 重抿 token"、 "wcx login 失效"、"最近十天的文章"。
version: 0.1.0
---

# wxmp-cracker (encrypted)

This skill's real instructions are encrypted. To use it, decrypt them first:

```bash
lovstudio-activate decrypt wxmp-cracker
```

**What to do:**

1. Run the command above.
2. The output is the actual SKILL.md for wxmp-cracker. Read it as if it were these instructions, and follow it to the letter.
3. If the command prints `error: not activated`, tell the user:
   > This is a paid Lovstudio skill. You need to activate it first:
   > ```
   > lovstudio-activate activate <your-license-key>
   > ```
   > If you don't have a license key, follow the 手工川 (ShougongChuan) WeChat official account to purchase one.
4. If the command prints `error: skill 'wxmp-cracker' not installed`, it means `~/.lovstudio/brand_skills/wxmp-cracker/` is empty. Tell the user to re-run `npx skills add lovstudio/skills` or to install the `lovstudio-activate` CLI (`pipx install lovstudio-activate`).
5. Do NOT cache the decrypted output between invocations — always re-decrypt on each use. The decryption is cheap (one HTTP round-trip) and re-running guarantees the user's license is still valid.

The encrypted payload lives in `~/.lovstudio/brand_skills/wxmp-cracker/` (or alongside this file, whichever the CLI finds). You don't need to touch it directly — just call `lovstudio-activate decrypt wxmp-cracker`.
