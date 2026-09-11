---
name: lov-feedback-loop
description: 把用户对 Agent 的被动情绪与主动点赞、点踩、评分变成可统计的反馈事件， 按任务、技能、规则、全局 Prompt 的最小作用域迭代，并生成满意度复盘报告。 Use when the user rates a run, asks for satisfaction stats, or installs the feedback loop into another agent.
version: 0.2.0
---

# 反馈飞轮 (encrypted)

本 Skill 的真实指令是加密的。使用前先解密：

```bash
uvx lovstudio-skill-helper decrypt feedback-loop
```

**What to do:**

1. 运行上面的命令。
2. 输出就是真正的 SKILL.md，把它当作本 Skill 的指令逐条执行。
3. 如果输出 `error: not activated` 或 `error: not logged in`，告诉用户：
   > 这是一个 Lovstudio 付费 skill，请先激活（CLI 会打开浏览器让你登录，然后绑定你的 license key）：
   > ```
   > npx lovstudio license <your-license-key>
   > ```
   > 还没有 license key？前往 https://lovstudio.ai/skills/feedback-loop 购买，或关注 #公众号：手工川 购买。
4. 如果输出 `error: not entitled`，helper 会交互式提示用户（输入 license key、打开购买页、或取消），让用户自己选。
5. 如果输出 `error: skill 'feedback-loop' not installed`，说明加密包还没装：
   > ```
   > npx lovstudio skills add feedback-loop                      # recommended: also checks deps
   > npx skills add lovstudio/skills --skill feedback-loop       # raw alternative
   > ```
6. 不要缓存解密结果：每次调用都重新解密，成本只有一次 HTTP 往返，同时保证授权仍然有效。
7. 解密出的 SKILL.md 会引用其他文件（如 `references/protocol.md`、`scripts/feedback_store.py`）。
   不要用 Read 工具直接读磁盘上的同名文件——它们只有密文 `.enc`。按需解密或用 exec 运行：
   ```bash
   uvx lovstudio-skill-helper decrypt feedback-loop references/protocol.md
   uvx lovstudio-skill-helper exec feedback-loop scripts/feedback_store.py stats --since 30d
   ```
   需要 lovstudio-skill-helper ≥ 0.9.0；更早的版本只能解密 SKILL.md。

加密包会落在 `~/.agents/skills/`、`~/.codex/skills/`、`~/.claude/skills/` 等目录下的
`lov-feedback-loop/`。你不用直接碰它，统一用
`uvx lovstudio-skill-helper decrypt feedback-loop [<相对路径>]` 读取，
需要运行脚本时用 `uvx lovstudio-skill-helper exec feedback-loop <相对路径> [参数...]`。
