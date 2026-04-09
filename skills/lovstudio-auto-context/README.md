# AutoContext

Automatic context hygiene for Claude Code sessions.

## What It Does

Monitors conversation length. When the transcript gets long, it nudges Claude to assess whether the current context is still relevant — and suggest `/fork` or `/btw` if it's not.

```
You (turn 1-30): implement auth feature
You (turn 31):   "now do the payment page"
                  ↑ AutoContext fires here
Claude:          "Different domain — I'd suggest /fork for a clean context."
```

## Install

This skill works best with the [lovstudio plugin](https://github.com/lovstudio/claude-code-plugin) which provides the auto-trigger hook. Without the plugin, use `/auto-context` for manual checks.

```bash
# Skill only (manual mode)
npx skills add lovstudio/skills --skill lovstudio:auto-context

# Full experience (auto mode + manual mode)
# Enable the lovstudio plugin in Claude Code
```

## Manual Use

Type `/auto-context` for a context health report at any time.

## How It Works

```
User submits prompt
        │
        ▼
 ┌──────────────┐
 │ Hook fires    │── transcript < threshold ──→ silent exit
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
