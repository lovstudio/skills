# Templates

## SKILL.md Template

```yaml
---
name: lovstudio:<name>
description: >
  <What it does — 1-2 sentences.>
  <When to trigger — specific scenarios, file types, user phrases.>
  Also trigger when the user mentions "<中文触发词>", "<english trigger>".
license: MIT
compatibility: >
  Requires Python 3.8+ and <library> (`pip install <library>`).
  Cross-platform: macOS, Windows, Linux.
metadata:
  author: lovstudio
  version: "1.0.0"
  tags: <space-separated tags>
---

# <name> — <Short Title>

<1-2 sentence overview.>

## When to Use

- <Scenario 1>
- <Scenario 2>

## Workflow (MANDATORY)

### Step 1: <First action>

```bash
python lovstudio-<name>/scripts/<script>.py --flag value
```

### Step 2: Ask the user

**Use `AskUserQuestion` to collect options BEFORE running.**

### Step 3: Execute

```bash
python lovstudio-<name>/scripts/<script>.py --input <path> --output <path>
```

## CLI Reference

| Argument | Default | Description |
|----------|---------|-------------|
| `--input` | (required) | ... |
| `--output` | `output.ext` | ... |

## Dependencies

```bash
pip install <library> --break-system-packages
```
```

## README.md Template

```markdown
# lovstudio:<name>

<One-line description.>

Part of [lovstudio/skills](https://github.com/lovstudio/skills) — by [lovstudio.ai](https://lovstudio.ai)

## Install

```bash
npx skills add lovstudio/skills --skill lovstudio:<name>
```

Requires: Python 3.8+ and `pip install <library>`

## Usage

```bash
python <script>.py --input file.ext --output result.ext
```

## Options

| Option | Default | Description |
|--------|---------|-------------|
| `--input` | (required) | ... |
| `--output` | `output.ext` | ... |

## License

MIT
```
