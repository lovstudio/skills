---
name: auto-context
description: >
  Manual context hygiene check. Analyzes current session for context pollution
  (long conversations, topic drift, stale noise) and recommends actions:
  continue, compress, /fork, /btw, or new session.
---

# AutoContext: Manual Context Health Check

When the user invokes `/auto-context`, perform a full context health report:

## Step 1: Measure

- Estimate how many user turns and tool calls are in the current session
- Identify the main topics/tasks discussed so far
- Note any obviously stale context (resolved errors, abandoned approaches, old debug output)

## Step 2: Assess

| Signal | Indicator |
|--------|-----------|
| Healthy | < 20 turns, single coherent topic |
| Getting noisy | 20-50 turns, or 2+ distinct topics with leftover artifacts |
| Polluted | 50+ turns, or significant stale context from earlier tasks |
| Critical | Near context window limit, compaction already happened |

## Step 3: Recommend

Based on assessment, recommend ONE action:

- **Continue** — context is clean, no action needed
- **Ignore noise** — some stale context exists but manageable, just proceed carefully
- **`/fork`** — create a clean branch, preserving current code state
- **`/btw`** — if user's request is a quick tangent, use btw to avoid pollution
- **New session** — context is heavily polluted, suggest starting fresh

## Rules

- Be concise. The whole report should be 3-5 lines.
- Don't be alarmist. Many sessions work fine at 40+ turns.
- Focus on actionable advice, not metrics.
