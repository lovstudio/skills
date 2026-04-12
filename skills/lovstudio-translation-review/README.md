# lovstudio:translation-review

Systematic Chinese-to-English translation review. Compares source and translation across 6 dimensions, produces a prioritized review report.

Part of [lovstudio/skills](https://github.com/lovstudio/skills) — by [lovstudio.ai](https://lovstudio.ai)

## Install

```bash
npx skills add lovstudio/skills --skill lovstudio:translation-review
```

Requires: `pandoc` for .docx support (`brew install pandoc`)

## Usage

Provide a Chinese source file and its English translation, then ask for review:

```
User: 请帮我审校这篇论文的英文翻译 @中文原文.docx @英文版本.docx
User: Check the translation quality of these two files
User: /translation-review
```

## What It Checks

| Dimension | What's Checked |
|-----------|---------------|
| Mistranslation | Meaning changes, omissions, additions |
| Terminology | Domain terms, abbreviations, proper nouns |
| Grammar | Articles, tense, agreement, syntax |
| Consistency | Same term → same translation throughout |
| References | Citation numbering, format, completeness |
| Style | Academic register, verbosity, paragraph structure |

## Output

A structured Markdown report with:
- **A-level** issues (must fix) — meaning errors, terminology mistakes
- **B-level** issues (recommended) — grammar polish, style improvements
- **C-level** issues — problems in the Chinese source itself
- Priority summary table
- Actionable fix suggestions for every issue

## Supported Formats

- `.docx` (requires pandoc)
- `.md`
- `.txt`

## License

MIT
