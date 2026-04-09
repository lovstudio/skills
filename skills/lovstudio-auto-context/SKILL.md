---
name: lovstudio:auto-context
description: >
  Manual context hygiene check. Analyzes current session for context pollution
  (long conversations, topic drift, stale noise) and recommends: continue,
  /fork, /btw, or new session. Also auto-triggered via UserPromptSubmit hook
  when installed as part of the lovstudio plugin.
license: MIT
compatibility: claude-code
metadata:
  author: Mark (手工川)
  repo: https://github.com/lovstudio/skills
---

# AutoContext: Context Health Check

## Auto Mode (via Plugin Hook)

When the lovstudio plugin is enabled, a `UserPromptSubmit` hook automatically
monitors transcript size. When thresholds are exceeded (40+ entries or 150KB+),
it injects a lightweight `<auto-context>` reminder asking you to assess context
relevance before proceeding.

**When you see `<auto-context>`:**

| Context State | Action |
|---------------|--------|
| Mostly relevant | Continue normally, say nothing |
| Some stale noise | Mentally deprioritize old context, proceed |
| Mostly irrelevant | Suggest: "Different topic — consider `/fork` or `/btw`" |
| Near capacity | Suggest: "Long session — consider `/fork` to start fresh" |

Rules:
- 1 sentence max. Don't waste the user's time.
- If context is fine, say nothing about it.
- Never auto-fork. Only suggest. User decides.
- Don't mention "AutoContext" unless user asks.

## Manual Mode (`/auto-context`)

When user invokes `/auto-context`, give a full context health report:

1. **Measure** — estimate turns, tool calls, distinct topics in current session
2. **Assess** — healthy / getting noisy / polluted / critical
3. **Recommend** — continue / `/fork` / `/btw` / new session

Keep the whole report to 3-5 lines. Focus on actionable advice, not metrics.
