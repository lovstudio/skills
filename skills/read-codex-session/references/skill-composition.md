# Nearby Skills Inspected
- `open-codex-session-skill`: 打开或导航任务。
- `codex-thread-usage-skill`: 统计 token 用量。

# Atomic Handoffs
导航需求可把 thread ID 交给 open skill；token 需求可交给 usage skill。

# Overlap Decisions
本 Skill 只负责读取状态与摘要，不拥有导航或 token 统计。

# Composition Decision
Single Skill；读取会话是一个完整结果，无需嵌套模块。
