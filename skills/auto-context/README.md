# AutoContext

![Version](https://img.shields.io/badge/version-0.4.0-CC785C)

Context operator for Claude Code sessions — not just a health check.

## What It Does

Three capability layers, routed by action sensitivity:

- **Auto-execute**: writes project memory when it spots unpersisted
  feedback/preferences; updates `MEMORY.md` index.
- **Confirm-first**: edits the configured global instructions file or project `CLAUDE.md`
  with a shown diff and explicit "yes" before applying.
- **Suggest-only**: harness commands like `/fork`, `/compact`, `/btw` —
  surfaced as exact-paste strings.

```
You (turn 31):  "从今以后所有输出都要带路径"
                 ↑ AutoContext writes feedback memory automatically

You (turn 45):  "/lov-auto-context 记到全局"
                 ↑ Shows diff of proposed global instructions edit, waits for yes

You (turn 80):  transcript size crosses threshold
                 ↑ Suggests: paste `/fork` (harness owns this one)
```

## Install

```bash
npx skills add auto-context -g -y
```

Works standalone as a manual skill. Auto-trigger on long transcripts
requires the [skill-publisher plugin](https://example.com/skills/claude-code-plugin)
which registers the `UserPromptSubmit` hook.

## Manual Use

```
/lov-auto-context                              # health report + opportunistic memory write
/lov-auto-context 记到全局                      # edit configured global instructions with confirm
/lov-auto-context 记到项目                      # edit project CLAUDE.md with confirm
/lov-auto-context 记住 X                        # write project memory
/lov-auto-context 该分叉了吗                    # evaluate + suggest /fork
```

## What It Cannot Do

Harness-owned commands (`/fork`, `/compact`, `/btw`, `/clear`, new
session) can't be invoked programmatically. The skill will print the
exact command for you to paste.

## User Configuration

Set `SKILL_AUTO_CONTEXT_AGENT_HOME` or configure
`${SKILL_PROFILE_PATH:-$HOME/.skill-publisher/skills/profile.json}` with
`agent.home`, `claude.home`, or `runtime.agent_home`. If none is available, the
skill asks once before editing global files.

## Version

0.3.0 — resolves agent home through env/profile/user input instead of a fixed
runtime directory. See [CHANGELOG.md](CHANGELOG.md).

## License

MIT
