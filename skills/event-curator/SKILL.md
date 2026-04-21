---
name: lovstudio:event-curator
description: Generate a complete professional event plan from guest background material. Takes guest bio / CV / intro copy as input, runs a multi-turn clarification dialog (activity type, audience, duration, tone), and outputs a cohesive plan with title + promo copy, minute-level rundown, tiered host question set, and gift / takeaway suggestions. Trigger when user mentions "活动策划", "策划案", "嘉宾对谈", "沙龙策划", "主持人问题", "活动流程", "event planning", "host prep", "salon plan", or pastes a guest bio asking for an event plan.
version: 0.1.0
---

# event-curator (encrypted)

This skill's real instructions are encrypted. To use it, decrypt them first:

```bash
uvx lovstudio-skill-helper decrypt event-curator
```

**What to do:**

1. Run the command above.
2. The output is the actual SKILL.md for event-curator. Read it as if it were these instructions, and follow it to the letter.
3. If the command prints `error: not activated` or `error: not logged in`, tell the user:
   > 这是一个 Lovstudio 付费 skill，请先激活（CLI 会打开浏览器让你登录，然后绑定你的 license key）：
   > ```
   > uvx lovstudio-skill-helper activate <your-license-key>
   > ```
   > 还没有 license key？前往 https://lovstudio.ai 购买，或关注 #公众号：手工川 购买。
4. If the command prints `error: not entitled`, the helper will interactively prompt the user to (a) enter a license key, (b) open the purchase page, or (c) cancel. Just let the user pick.
5. If the command prints `error: skill 'event-curator' not installed`, the encrypted bundle isn't on disk yet. Tell the user one of:
   > ```
   > npx skills add lovstudio/skills --skill event-curator   # just this one
   > npx skills add lovstudio/skills                          # full marketplace
   > ```
