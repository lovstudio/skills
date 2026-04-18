# AutoContext

Context operator for Claude Code sessions — not just a health check.

## What It Does

Three capability layers, routed by action sensitivity:

- **Auto-execute**: writes project memory when it spots unpersisted
  feedback/preferences; updates `MEMORY.md` index.
- **Confirm-first**: edits `~/.claude/CLAUDE.md` or project `CLAUDE.md`
  with a shown diff and explicit "yes" before applying.
- **Suggest-only**: harness commands like `/fork`, `/compact`, `/btw` —
  surfaced as exact-paste strings.

```
You (turn 31):  "从今以后所有输出都要带路径"
                 ↑ AutoContext writes feedback memory automatically

You (turn 45):  "/lovstudio-auto-context 记到全局"
                 ↑ Shows diff of proposed ~/.claude/CLAUDE.md edit, waits for yes

You (turn 80):  transcript size crosses threshold
                 ↑ Suggests: paste `/fork` (harness owns this one)
```

## Install

Works standalone as a manual skill. Auto-trigger on long transcripts
requires the [lovstudio plugin](https://github.com/lovstudio/claude-code-plugin)
which registers the `UserPromptSubmit` hook.

## Manual Use

```
/lovstudio-auto-context                              # health report + opportunistic memory write
/lovstudio-auto-context 记到全局                      # edit ~/.claude/CLAUDE.md with confirm
/lovstudio-auto-context 记到项目                      # edit project CLAUDE.md with confirm
/lovstudio-auto-context 记住 X                        # write project memory
/lovstudio-auto-context 该分叉了吗                    # evaluate + suggest /fork
```

## What It Cannot Do

Harness-owned commands (`/fork`, `/compact`, `/btw`, `/clear`, new
session) can't be invoked programmatically. The skill will print the
exact command for you to paste.

## Version

0.2.0 — adds confirm-first editing of global/project CLAUDE.md and
auto-write of feedback memory. See [CHANGELOG.md](CHANGELOG.md).

## License

MIT
