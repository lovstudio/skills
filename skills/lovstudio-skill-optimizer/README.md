# lovstudio:skill-optimizer

![Version](https://img.shields.io/badge/version-0.3.0-CC785C)

自动优化 lovstudio skill — 审计规范、应用修复、bump 版本、追加 changelog。

Part of [lovstudio/skills](https://github.com/lovstudio/skills) — by [lovstudio.ai](https://lovstudio.ai)

## Install

```bash
npx skills add lovstudio/skills --skill lovstudio:skill-optimizer
```

Requires: Python 3.8+ (stdlib only, no `pip install`)

## What It Does

```
┌──────────────────────────────────────────────────┐
│             skill-optimizer pipeline             │
├──────────────────────────────────────────────────┤
│  1. lint       审计 SKILL.md / scripts / README  │
│  2. apply      优先修复对话中提到的问题          │
│  3. bump       patch / minor / major             │
│  4. changelog  追加 Keep a Changelog 条目        │
│  5. re-lint    验证 + 输出简报                   │
│  6. commit     git add + commit + push           │
└──────────────────────────────────────────────────┘
```

Fully automatic — no interactive prompts. Optimizations are driven by issues
raised in the current conversation, supplemented by a generic lint pass.

## Usage

### In Claude Code

```
/lovstudio:skill-optimizer any2pdf

# or with explicit focus:
/lovstudio:skill-optimizer any2pdf — the --theme flag trigger phrase is wrong
```

Claude will:
1. Run `lint_skill.py` for a baseline audit.
2. Read any conversation context about problems the user hit with this skill.
3. Edit `SKILL.md` / `README.md` / scripts to fix prioritized issues.
4. Run `bump_version.py` to bump the version and prepend a `CHANGELOG.md` entry.
5. Report what changed.
6. Commit and push to GitHub.

### CLI

Audit only:

```bash
python3 scripts/lint_skill.py any2pdf
python3 scripts/lint_skill.py any2pdf --json
```

Bump version and write changelog:

```bash
python3 scripts/bump_version.py any2pdf \
  --type patch \
  --message "fix CJK line-wrap in bullet lists" \
  --change "tighten frontmatter trigger phrases"
```

Dry run (show without writing):

```bash
python3 scripts/bump_version.py any2pdf --type patch -m "..." --dry-run
```

## What Gets Audited

| Check | Severity | What it catches |
|-------|----------|-----------------|
| Directory prefix `lovstudio-` | error | Wrong dir naming |
| `SKILL.md` / `README.md` present | error | Missing core files |
| Frontmatter required fields | error | Missing `name` / `description` / `license` / `compatibility` / `metadata` |
| `name` matches directory | error | `lovstudio:foo` vs `lovstudio-bar` drift |
| Description has trigger cues | warn | Missing "Use when..." or "trigger when user mentions..." |
| Description length | warn | < 80 chars likely insufficient |
| `metadata.version` semver format | warn | Non-`x.y.z` versions |
| README version badge | warn | Missing `![Version](...)` |
| README install command | warn | Missing `npx skills add ...` |
| `CHANGELOG.md` exists | warn | No changelog |
| Scripts use argparse | warn | CLI without argparse |
| SKILL.md body length | warn | > 500 lines — should split to `references/` |
| TODO placeholders | error | Uninitialized template content |
| CJK handling for doc skills | info | Document skills without visible CJK code paths |

## Version Bump Rules

| Bump | When to use |
|------|-------------|
| `patch` | bug fix, wording, frontmatter tweak, CJK rendering fix |
| `minor` | new flag/option/reference doc, expanded scope |
| `major` | breaking CLI change, removed option, rename |

Per repo convention: stay in `0.x` unless explicitly authorized.

## Options

### `lint_skill.py`

| Option | Default | Description |
|--------|---------|-------------|
| `<name>` | — | Skill name (with/without `lovstudio-` prefix) |
| `--path` | — | Absolute path to skill dir |
| `--json` | off | Emit JSON |

### `bump_version.py`

| Option | Default | Description |
|--------|---------|-------------|
| `<name>` | — | Skill name |
| `--path` | — | Absolute path (overrides name) |
| `--type` | — | `patch` / `minor` / `major` |
| `--set` | — | Explicit version e.g. `0.2.0` |
| `--message`, `-m` | required | Primary changelog bullet |
| `--change`, `-c` | — | Additional bullet (repeatable) |
| `--dry-run` | off | Preview without writing |

## License

MIT
