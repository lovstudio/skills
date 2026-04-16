# lovstudio:visual-clone

![Version](https://img.shields.io/badge/version-1.0.1-CC785C)

Extract design DNA from a reference image and generate a reusable replication prompt.

Part of [lovstudio/skills](https://github.com/lovstudio/skills) — by [lovstudio.ai](https://lovstudio.ai)

## Install

```bash
npx skills add lovstudio/skills --skill lovstudio:visual-clone
```

No dependencies — pure AI visual analysis.

## Usage

Provide a reference design image and say:

- "复刻这个风格"
- "提取设计要素"
- "analyze this design"
- `/visual-clone`

The skill will:

1. Ask what scenario you want to apply the style to
2. Analyze the image across 8 dimensions (layout, color, typography, style, texture, imagery, copy, spacing)
3. Output a structured **Design DNA** document with hex colors, font specs, spacing patterns
4. Generate a **Replication Prompt** you can paste into any downstream tool (AI image gen, design brief, brand guide)

## Output Example

```
## Design DNA

### Color Palette / 色彩
- Primary: #CC785C (陶土色) — 40%
- Background: #F9F9F7 (暖米色) — 45%
- Text: #181818 (炭灰) — 15%
- Mood: warm, earthy, academic

### Typography / 字体
- Headline: Noto Serif CJK (宋体), Bold, ~32px
- Body: Inter / Noto Sans, Regular, ~14px
- Tight letter-spacing, 1.6 line-height
...

## Replication Prompt / 复刻指令
[Self-contained brief ready to paste]
```

## License

MIT
