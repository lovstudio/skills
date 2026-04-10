# lovstudio:anti-wechat-ai-check

检测文章 AI 生成痕迹，输出风险评分，并可人性化润色以通过微信公众号 3.27 条款检测。

Part of [lovstudio/skills](https://github.com/lovstudio/skills) — by [lovstudio.ai](https://lovstudio.ai)

## Install

```bash
npx skills add lovstudio/skills --skill lovstudio:anti-wechat-ai-check
```

Requires: Python 3.8+ (no external dependencies)

## What It Checks

```
┌─────────────────────────────────────────────┐
│              AI 痕迹分析引擎                  │
├─────────────────────────────────────────────┤
│  模板短语检测    "随着...不断发展" etc.        │
│  过渡词密度      首先/其次/此外 占比           │
│  句子长度均匀度  变异系数 < 0.25 = 可疑        │
│  段落长度均匀度  段段等长 = 模板生成            │
│  段首/句首重复   重复 ≥ 3 次 = 套路            │
│  "的"字密度      > 6% = AI 常见过度使用        │
│  列举模式        过度条理化                    │
├─────────────────────────────────────────────┤
│  输出: 风险评分 0-100 + 逐项问题清单          │
└─────────────────────────────────────────────┘
```

## Usage

### CLI

```bash
# 分析文件
python analyze.py --input article.md

# 分析内联文本
python analyze.py --text "你的文章内容"

# JSON 格式输出（供程序消费）
python analyze.py --input article.md --format json
```

### In Claude Code

```
/lovstudio:anti-wechat-ai-check

然后粘贴文章或提供文件路径
```

Claude 会自动运行分析、展示报告、提供人性化润色建议或直接输出修改版。

## Options

| Option | Default | Description |
|--------|---------|-------------|
| `--input`, `-i` | — | 输入文件路径 (.md, .txt) |
| `--text`, `-t` | — | 内联文本 |
| `--format`, `-f` | `text` | 输出格式: `text` / `json` |

## Risk Levels

| Score | Level | Meaning |
|-------|-------|---------|
| 0-24 | LOW | AI 特征不明显 |
| 25-49 | MEDIUM | 有一定 AI 痕迹，建议修改 |
| 50-100 | HIGH | AI 痕迹明显，大概率被检测 |

## License

MIT
