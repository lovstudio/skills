# Changelog

## 0.2.0 — 2026-04-18

- Expand scope from "hygiene checker" to **context operator** covering all
  context-affecting actions the skill can reach.
- Add action layer 1 (auto-execute): write project memory when unpersisted
  feedback/preferences are detected in the session.
- Add action layer 2 (confirm-first): edit `~/.claude/CLAUDE.md` or project
  `CLAUDE.md` with diff-preview-then-confirm flow.
- Add action layer 3 (suggest-only): surface `/fork`, `/compact`, `/btw` as
  exact-paste strings. Document that harness owns these — skill can't
  invoke them.
- Add argument-parsing for targeted ops: "记到全局", "记到项目", "记住 X",
  "忘掉 X", "该分叉了吗".
- Output-path convention: every file-writing action echoes absolute +
  relative path.

## 0.1.0

- Initial release: hook-triggered `<auto-context>` nudge + manual
  `/lovstudio-auto-context` health report.
