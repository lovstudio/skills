# AutoContext Plugin

Automatic context hygiene for Claude Code sessions.

## What It Does

A `UserPromptSubmit` hook monitors your conversation length. When the transcript gets long (40+ entries or 150KB+), it injects a lightweight prompt asking Claude to assess whether the current context is still relevant to your new request — and suggest `/fork` or `/btw` if it's not.

```
You (turn 1-30): implement auth feature ✓
You (turn 31):   "now do the payment page"
                  ↑ AutoContext fires here
Claude:          "This is a different domain. I'd suggest /fork for a clean context."
```

## Install

```bash
# Via plugin marketplace (when published)
claude plugin install auto-context

# Local development
claude --plugin-dir ./plugins/auto-context
```

## Manual Use

Type `/auto-context` for a full context health report at any time.

## Configuration

Edit `scripts/context_sense.py` to tune thresholds:

| Variable | Default | Meaning |
|----------|---------|---------|
| `LINE_THRESHOLD` | 40 | Transcript entries before first trigger |
| `SIZE_THRESHOLD` | 150,000 | Transcript bytes (~150KB) |
| `COOLDOWN_ENTRIES` | 10 | Min entries between re-triggers |

## How It Works

```
User submits prompt
        │
        ▼
 ┌──────────────┐
 │ Hook fires    │──── transcript < threshold ──→ silent exit
 │ context_sense │
 └──────┬───────┘
        │ threshold exceeded
        ▼
 Inject <auto-context> reminder
        │
        ▼
 Claude assesses relevance
        │
   ┌────┴────┐
   ▼         ▼
 Clean?    Polluted?
 Continue  Suggest /fork or /btw
```

## License

MIT
