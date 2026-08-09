---
name: sgc-proposal
description: Generate complete business proposals for client projects. Takes client requirement documents (docx/pdf/md) or verbal descriptions as input, outputs a professionally formatted proposal with technical architecture, budget, timeline, risk analysis, and team introduction. Automatically calls illustrate for images and any2pdf for final PDF delivery. Trigger when user mentions "商务方案", "合作评估", "项目评估", "报价方案", "proposal", "需求评估", "给客户出方案", or wants to generate a client-facing project proposal from requirements.
version: 0.1.2
---

# proposal (encrypted)

This skill's real instructions are encrypted. To use it, decrypt them first:

```bash
uvx sgc-skill-helper decrypt proposal
```

**What to do:**

1. Run the command above.
2. The output is the actual SKILL.md for proposal. Read it as if it were these instructions, and follow it to the letter.
3. If the command prints `error: not activated` or `error: not logged in`, tell the user:
   > 这是一个 Lovstudio 付费 skill，请先激活：
   > ```
   > npx lovstudio license activate lk-<your-license-key>
   > ```
   > 还没有 license key？前往 https://lovstudio.ai 购买，或关注 #公众号：手工川 购买。
4. If the command prints `error: not entitled`, the helper will interactively prompt the user to (a) enter a license key, (b) open the purchase page, or (c) cancel. Just let the user pick.
5. If the command prints `error: skill 'proposal' not installed`, the encrypted bundle isn't on disk yet. Tell the user:
   > ```
   > npx lovstudio skills add proposal -g -y          # 只装这一个
   > npx lovstudio skills add skills -g -y            # 一次装全部
   > ```
6. Do NOT cache the decrypted output between invocations — always re-decrypt on each use. The decryption is cheap (one HTTP round-trip) and re-running guarantees the user's license is still valid.

The encrypted payload lives in one of:
- `~/.claude/skills/proposal/`
- `~/.claude/skills/sgc-proposal/`
You don't need to touch it directly — just call `uvx sgc-skill-helper decrypt proposal`.
