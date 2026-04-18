# lovstudio:gh-contribute

![Version](https://img.shields.io/badge/version-0.1.0-CC785C)

Contribute a clean, professional PR to someone else's GitHub repo — fork, branch,
commit, push, open PR. Auto-splits unrelated changes into separate PRs.

Part of [lovstudio skills](https://github.com/lovstudio/skills) — by [lovstudio.ai](https://lovstudio.ai)

## Install

```bash
git clone https://github.com/lovstudio/gh-contribute-skill ~/.claude/skills/lovstudio-gh-contribute
```

Requires: [`gh` CLI](https://cli.github.com/) (authenticated via `gh auth login`) and `git`.
No Python dependencies.

## Usage

Invoke from Claude Code in a repo you want to contribute to:

```
/lovstudio:gh-contribute
```

Or just describe the intent:

> 给 ZenMux/zenmux-doc 提个 PR，把 CLAUDE.md 的 script 列表改掉

The skill will:

1. Detect the upstream `owner/repo` and default branch
2. Read `CONTRIBUTING.md` / PR templates for house rules
3. Survey your changes and propose a PR plan (single or split)
4. Ask you to confirm the plan
5. Fork, branch, commit, push, and open PR(s)
6. Cross-link related PRs when splitting

## When to split into multiple PRs

The skill prefers a single PR when changes are cohesive and under ~300 lines.
It suggests splitting when it sees:

- Docs + code changes mixed (ship docs fast, code reviews slower)
- Refactor + feature (refactor lands first, feature on top)
- Unrelated subsystems touched
- One change is trivially correct, another needs discussion

You always confirm the plan before anything is pushed.

## What it won't do

- Write the code changes for you — assumes the working tree already has edits
- Push to upstream — always pushes to your fork
- Force-push over existing review comments
- Bypass hooks / CI / signing unless you explicitly ask

## License

MIT
