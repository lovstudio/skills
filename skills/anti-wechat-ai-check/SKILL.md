---
name: lovstudio:anti-wechat-ai-check
category: Content Processing
tagline: "检测文章 AI 痕迹 + 人性化润色，通过微信 3.27 条款检测。"
description: >
  Analyze articles for AI-generated content indicators and rewrite to pass
  WeChat's 3.27 non-human automated content creation detection. Checks for
  template phrases, transition word density, sentence uniformity, paragraph
  pattern repetition, and other signals that WeChat uses to flag AI content.
  Outputs a risk report and an optional humanized rewrite. Use when the user
  wants to check if an article looks AI-generated, make an article more
  human-like, bypass WeChat AI detection, or humanize AI-written content.
  Also trigger when the user mentions "去AI痕迹", "人性化润色", "微信AI检测",
  "anti-ai-check", "humanize article", "公众号发文检查".
license: MIT
compatibility: >
  Requires Python 3.8+ (stdlib only, no external dependencies).
  Cross-platform: macOS, Windows, Linux.
metadata:
  author: lovstudio
  version: "1.0.0"
  tags: wechat ai-detection humanize content-review
---

# anti-wechat-ai-check — 微信公众号 AI 痕迹检测与人性化润色

检测文章中的 AI 生成痕迹（模板短语、过渡词堆砌、句式雷同等），给出风险
评分和修改建议，并可输出人性化润色后的版本。基于微信公众平台运营规范
3.27 条款（非真人自动化创作行为）的检测逻辑。

## When to Use

- 用户准备将 AI 辅助写作的文章发布到微信公众号
- 用户想检查一篇文章是否有明显 AI 痕迹
- 用户想将 AI 生成的草稿改写为更自然的人类风格

## Workflow (MANDATORY)

**You MUST follow these steps in order:**

### Step 1: Get the article

Determine the input source:
- If user provides a **file path** → read the file
- If user **pastes text** in the conversation → save to a temp file or use `--text`

### Step 2: Run analysis

```bash
python skills/lovstudio-anti-wechat-ai-check/scripts/analyze.py \
  --input <path> --format json
```

Or with inline text:

```bash
python skills/lovstudio-anti-wechat-ai-check/scripts/analyze.py \
  --text "文章内容" --format json
```

### Step 3: Present findings

Show the user:
1. **Risk score** (0-100) and risk level (LOW / MEDIUM / HIGH)
2. **Template phrases found** — list each one with its location
3. **Structure issues** — transition word density, paragraph uniformity, etc.
4. **Sentence issues** — length uniformity, repeated starters, excessive "的"

### Step 4: Ask the user

**IMPORTANT: Use `AskUserQuestion` to ask what to do next:**

| Option | Description |
|--------|-------------|
| 仅查看报告 | 用户自己修改，skill 结束 |
| 给出修改建议 | 列出每个问题的具体修改建议，不改原文 |
| 直接输出修改版 | 输出人性化润色后的完整文章 |

### Step 5: Humanize (if requested)

When rewriting, follow these **humanization rules**:

#### 5a. 消除模板短语
- 删除或替换报告中标出的每个模板短语
- "随着科技的不断发展" → 直接说具体的事（"去年 ChatGPT 发布后..."）
- "综上所述" → 删掉，或换成口语化的收尾

#### 5b. 降低过渡词密度
- 目标：过渡词密度 < 15%
- 删除不必要的 "首先/其次/此外/另外"
- 用具体的逻辑关系替代泛化连接词

#### 5c. 打破句式均匀
- 刻意制造长短句交替：短句 < 15 字，长句 > 40 字
- 加入口语化表达、反问句、感叹句
- 偶尔使用不完整句或省略句

#### 5d. 打破段落均匀
- 有的段落只有一两句话，有的段落可以很长
- 避免每段都是 "论点 + 论据 + 小结" 的三段式

#### 5e. 增加人味
- 加入个人经历、具体案例、数字细节
- 使用口语化表达（"说白了"、"讲真"、"你想想"）
- 适当使用不规范但自然的表达
- 减少 "的" 字使用（目标 < 5%）

#### 5f. 保留原意
- 核心观点和信息不能丢失
- 专业术语保留，不要过度口语化
- 保持原文的立场和态度

### Step 6: Output

Output the humanized article as markdown. If the input was a file, also offer
to write the result back to a file (with `-humanized` suffix).

## CLI Reference

| Argument | Default | Description |
|----------|---------|-------------|
| `--input`, `-i` | — | Input file path (.md, .txt) |
| `--text`, `-t` | — | Inline text to analyze |
| `--format`, `-f` | `text` | Output format: `text` or `json` |

## Dependencies

No external dependencies — stdlib only.
