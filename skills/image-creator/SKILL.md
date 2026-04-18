---
name: lovstudio:image-creator
category: Image & Design
tagline: "Multi-mechanism image generation: end-to-end AI, code rendering, or prompt engineering"
description: >
  Generate images via multiple mechanisms. Supports:
  (1) End-to-end AI generation via Gemini/ZenMux — given a prompt, directly output an image.
  (2) Code-based rendering — generate HTML/React single-file, render to PNG via Playwright.
  (3) Prompt engineering — generate optimized prompts for external models (nano-banana-pro, etc.).
  Trigger words: image, generate image, 生图, render, poster, 海报, banner, card, 卡片
allowed-tools: [Bash, Read, Write, Edit]
version: "0.2.0"
---

# Image Creator — Multi-Mechanism Framework

## Mechanism Selection

Choose the mechanism based on user intent:

| Mechanism | When to Use | Output |
|-----------|------------|--------|
| **end-to-end** | User wants AI-generated artwork, photos, illustrations | PNG image |
| **code** | User wants designed layouts (posters, cards, banners) with editable content | HTML file + PNG |
| **prompt** | User wants a prompt for external model (Midjourney, nano-banana-pro, etc.) | Text prompt |

If the user doesn't specify, infer from context:
- "生成一张猫的图片" → end-to-end
- "做一张活动海报" → code
- "帮我写一个 Midjourney prompt" → prompt

## Mechanism 1: End-to-End (Gemini)

```bash
python3 ~/.claude/skills/lovstudio-image-creator/gen_image.py "PROMPT" [-o output.png] [-q low|medium|high] [--ascii]
```

- Generates image directly via Gemini 3 Pro (through ZenMux)
- Requires `ZENMUX_API_KEY` environment variable
- First run auto-installs `google-genai` and `Pillow` via `pip --user` (no manual setup)
- Display result with `Read` tool after generation

## Mechanism 2: Code-Based Rendering

### Step 1: Generate HTML

Write a single self-contained HTML file that includes all styles inline. Use:
- **React 19** via CDN (`https://cdn.jsdelivr.net/npm/react@19/umd/react.production.min.js`)
- **ReactDOM 19** via CDN
- **Tailwind CSS** via CDN (`https://cdn.tailwindcss.com`)
- **Google Fonts** via `<link>` for CJK: `Noto Sans SC`, `Noto Serif SC`

Template structure:

```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <script src="https://cdn.jsdelivr.net/npm/react@19/umd/react.production.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/react-dom@19/umd/react-dom.production.min.js"></script>
  <script src="https://cdn.tailwindcss.com"></script>
  <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;500;700;900&family=Noto+Serif+SC:wght@400;700&display=swap" rel="stylesheet">
  <script>
    tailwind.config = {
      theme: { extend: { /* custom theme */ } }
    }
  </script>
  <style>
    /* Reset & base styles */
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { width: {{WIDTH}}px; height: {{HEIGHT}}px; overflow: hidden; }
  </style>
</head>
<body>
  <div id="root"></div>
  <script type="text/babel" data-type="module">
    // React component here
    function Poster() {
      return (/* JSX */);
    }
    ReactDOM.createRoot(document.getElementById('root')).render(<Poster />);
  </script>
  <script src="https://cdn.jsdelivr.net/npm/@babel/standalone/babel.min.js"></script>
</body>
</html>
```

**IMPORTANT**: Babel standalone script MUST come AFTER the text/babel script block.

### Step 2: Render to PNG

```bash
python3 ~/.claude/skills/lovstudio-image-creator/scripts/render_to_png.py \
  /path/to/poster.html \
  -o output.png \
  -W 1200 -H 630 \
  --scale 2
```

Common aspect ratios:
| Ratio | Dimensions | Use Case |
|-------|-----------|----------|
| 16:9 | 1200×675 | Social media banner |
| 4:3 | 1200×900 | Presentation |
| 1:1 | 1080×1080 | Instagram post |
| 9:16 | 1080×1920 | Story / mobile poster |
| 3:4 | 900×1200 | Portrait poster |
| A4 | 794×1123 | Print poster (210mm×297mm @96dpi) |

### Step 3: Display & Iterate

- Use `Read` to display the PNG
- Open with `open output.png` on macOS
- User can request edits → modify the HTML → re-render

## Mechanism 3: Prompt Engineering

Generate optimized prompts for external models. Include:
- **Positive prompt**: subject, style, lighting, quality tags
- **Negative prompt**: common defects to avoid

Format output as copyable code block.

## Reference Image Support

When user provides a reference image:
- **End-to-end**: describe the style/composition in the prompt
- **Code**: analyze the layout, colors, typography → replicate in HTML/CSS
- **Prompt**: extract style keywords for the external model

## Aspect Ratio

Always ask or infer the desired aspect ratio. Map to pixel dimensions using the table above.
