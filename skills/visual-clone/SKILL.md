---
name: lovstudio:visual-clone
category: "Image & Design"
tagline: "Extract design DNA from reference images / 提取设计要素生成复刻指令"
description: >
  Analyze a reference design image and extract visual DNA — layout, style, color palette,
  texture, typography, copy tone, spacing, etc. — into a structured, reusable replication
  prompt that can be applied to new scenarios.
  Trigger when: user provides a reference image and asks to "extract style", "replicate this",
  "clone this design", "analyze this visual", "generate a replication prompt",
  "提取设计要素", "复刻这个风格", "分析这张图", "视觉克隆".
license: MIT
compatibility: >
  No dependencies. Pure AI visual analysis — requires a model with vision capability.
metadata:
  author: lovstudio
  version: "1.0.1"
  tags: design, visual-analysis, style-extraction, prompt-generation
---

# visual-clone — Design DNA Extractor

Given a reference design image, systematically extract every visual element and output
a structured replication prompt that can be used to recreate the style in a different context.

## When to Use

- User provides a design image (poster, card, banner, UI screenshot, social media graphic) and wants to replicate the style
- User wants to understand the visual language of a reference and apply it elsewhere
- User needs a structured design brief derived from an existing piece

## Workflow (MANDATORY)

**You MUST follow these steps in order:**

### Step 1: Receive the Reference Image

Read the image the user provides. If no image is given, use `AskUserQuestion` to ask them to provide one.

### Step 2: Ask Context

**Use `AskUserQuestion` to collect before analysis:**

Ask the user (single question):
- "你想把这个风格复刻到什么场景？（例如：另一张海报、社交媒体图、名片、PPT 封面、AI 生图 prompt……）如果还没想好也可以先提取，之后再套用。"

### Step 3: Analyze — Extract Design DNA

Examine the image and extract ALL of the following dimensions. Be specific, not vague.
Use concrete values (hex colors, approximate sizes, named fonts) wherever possible.

Output a structured Markdown document titled **"Design DNA"** with these sections:

#### 3.1 Layout / 布局
- Overall composition (grid, centered, asymmetric, layered, etc.)
- Content zones and their spatial relationships
- Alignment patterns, margins, padding estimates
- Visual hierarchy: what draws the eye first → second → third
- Aspect ratio

#### 3.2 Color Palette / 色彩
- Primary color(s) with hex values
- Secondary / accent colors with hex values
- Background color(s) / gradient description
- Color ratio (approximate % of each color in the composition)
- Color mood: warm / cool / neutral / contrasting

#### 3.3 Typography / 字体
- Headline font style (serif, sans-serif, script, display — name if recognizable)
- Body text font style
- Font weight / size hierarchy
- Letter-spacing, line-height feel (tight / normal / loose)
- Text color(s) and any text effects (shadow, outline, gradient fill)

#### 3.4 Visual Style / 视觉风格
- Design era / movement (e.g., Swiss modernism, Y2K, Japanese minimalism, brutalism)
- Illustration style if present (flat, 3D, hand-drawn, photographic, collage)
- Shape language (geometric, organic, angular, rounded)
- Border / divider treatment
- Icon style if present

#### 3.5 Texture & Material / 质感
- Surface feel (matte, glossy, paper grain, noise, fabric, metallic)
- Overlay effects (grain, halftone, blur, duotone)
- Shadow style (none, soft, hard, long, colored)
- Depth / dimensionality (flat, layered, 3D)

#### 3.6 Imagery / 图像处理
- Photo treatment (if any): filter, crop style, masking, blend mode
- Illustration integration method
- Decorative elements (patterns, stickers, stamps, badges)

#### 3.7 Copy & Tone / 文案风格
- Headline tone (formal, playful, poetic, provocative, minimal)
- Information density (sparse / moderate / dense)
- Language register and word choice style
- CTA style if present

#### 3.8 Spacing & Rhythm / 间距与节奏
- Overall density (airy / balanced / compact)
- White space usage pattern
- Repetition / rhythm of elements
- Breathing room between sections

### Step 4: Generate Replication Prompt

Based on the extracted DNA, generate **a single, self-contained replication prompt** in this format:

```markdown
## Replication Prompt / 复刻指令

### Visual Brief
[1-2 sentence summary of the overall visual identity]

### Specifications
- **Layout**: [composition description]
- **Color palette**: [hex values with roles]
- **Typography**: [font styles, hierarchy]
- **Style**: [era, mood, shape language]
- **Texture**: [material feel, effects]
- **Imagery**: [photo/illustration treatment]
- **Spacing**: [density, rhythm]
- **Copy tone**: [voice, register]

### When Applying to [user's target scenario]
[Specific adaptation notes for the user's stated scenario.
 What to keep exactly, what to adjust, what to substitute.]

### AI Image Generation Version (English)
[If applicable: a condensed English prompt optimized for
 Midjourney / DALL-E / Flux / Stable Diffusion style,
 under 200 words, focusing on visual descriptors]
```

### Step 5: Deliver

Output the full Design DNA analysis + Replication Prompt as a single Markdown document.

If the user specified a target scenario in Step 2, include concrete adaptation guidance.
If they said "先提取", skip the adaptation section and note they can come back to apply it later.

## Output Rules

- Color values MUST include hex codes, not just names
- Font identification: name the font if recognizable, otherwise describe the style precisely
- All section headers in **中英双语** format
- Technical terms in English, descriptions in Chinese
- Be specific over generic: "12px letter-spacing, tight leading" > "modern typography"
- The Replication Prompt should be **copy-pasteable** as a standalone brief

## No Scripts Needed

This skill is pure visual analysis. No Python scripts, no CLI tools.
