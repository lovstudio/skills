---
name: lov-any2deck
description: >
  Turn Markdown, text or URLs into slide decks in 17 styles, as AI slide images
  or an editable one-ink mono PPTX. Use when the user asks to "做PPT" or "生成幻灯片".
license: MIT
compatibility: >
  Requires an image generation skill (e.g. image-gen) and Node.js for PPTX/PDF merge.
  Python 3.8+ for branding overlay; the mono style needs python-pptx, Pillow and numpy.
  Cross-platform: macOS, Windows, Linux.
depends_on:
  - lov-branding-consistency
metadata:
  author: contributors
  version: "1.2.1"
  tags:
    - slide-deck
    - presentation
    - pptx
    - pdf
    - image-generation
---

# PPT 大师 · PPT Master

Transform content into professional slide deck images.

## Triggers

### Activate when

- 用户说“做PPT”“生成幻灯片”“制作演示文稿”“把这篇文章做成 slides”，或给出内容要求出一份 deck。
- The user asks to create slides, make a presentation, generate a deck, or restyle an existing deck.
- 用户点名某个风格（如 `mono`、`sketch-notes`）或要求“可编辑的 PPTX”“会议室投屏用的中文 PPT”。

### Do not activate when

- 只要把 Markdown 转成 PDF 或 Word：交给 `lov-any2pdf` / `lov-any2docx`。
- 只要一张海报、封面、信息图或单张卡片：交给对应的海报、封面或信息图 Skill。
- 只改现有 PPTX 里的几处文字或数据，不涉及生成或重排版。

## Usage

```bash
/lov-any2deck path/to/content.md
/lov-any2deck path/to/content.md --style sketch-notes
/lov-any2deck path/to/content.md --audience executives
/lov-any2deck path/to/content.md --lang zh
/lov-any2deck path/to/content.md --slides 10
/lov-any2deck path/to/content.md --outline-only
/lov-any2deck  # Then paste content
```

## Script Directory

**Agent Execution Instructions**:
1. Determine this SKILL.md file's directory path as `SKILL_DIR`
2. Script path = `${SKILL_DIR}/scripts/<script-name>`

| Script | Purpose |
|--------|---------|
| `scripts/merge-to-pptx.ts` | Merge slides into PowerPoint |
| `scripts/merge-to-pdf.ts` | Merge slides into PDF |
| `scripts/mono_pptx_kit.py` | mono 风格可编辑 PPTX 工具包（母版纸纹与 Logo、单色调图片、问题页、Q&A）；`--demo` 自检 |
| `scripts/apply-branding.py` | Composite logo(s)/QR onto slides — dual logo, tight-crop, JPG white→alpha (opt-in) |

## Options

| Option | Description |
|--------|-------------|
| `--style <name>` | Visual style: preset name, `custom`, or custom style name |
| `--audience <type>` | Target: beginners, intermediate, experts, executives, general |
| `--lang <code>` | Output language (en, zh, ja, etc.) |
| `--slides <number>` | Target slide count (8-25 recommended, max 30) |
| `--outline-only` | Generate outline only, skip image generation |
| `--prompts-only` | Generate outline + prompts, skip images |
| `--images-only` | Generate images from existing prompts directory |
| `--regenerate <N>` | Regenerate specific slide(s): `--regenerate 3` or `--regenerate 2,5,8` |
| `--logo <path>` | Primary brand logo (top-right, skips cover/back-cover) |
| `--logo2 <path>` | Secondary logo (placed left of primary, optically aligned) |
| `--presentation` | Presentation mode: strips narration text, keeps only visual anchors |

**Slide Count by Content Length**:
| Content | Slides |
|---------|--------|
| < 1000 words | 5-10 |
| 1000-3000 words | 10-18 |
| 3000-5000 words | 15-25 |
| > 5000 words | 20-30 (consider splitting) |

## Style System

### Presets

| Preset | Dimensions | Best For |
|--------|------------|----------|
| `blueprint` (Default) | grid + cool + technical + balanced | Architecture, system design |
| `chalkboard` | organic + warm + handwritten + balanced | Education, tutorials |
| `corporate` | clean + professional + geometric + balanced | Investor decks, proposals |
| `minimal` | clean + neutral + geometric + minimal | Executive briefings |
| `sketch-notes` | organic + warm + handwritten + balanced | Educational, tutorials |
| `watercolor` | organic + warm + humanist + minimal | Lifestyle, wellness |
| `dark-atmospheric` | clean + dark + editorial + balanced | Entertainment, gaming |
| `notion` | clean + neutral + geometric + dense | Product demos, SaaS |
| `bold-editorial` | clean + vibrant + editorial + balanced | Product launches, keynotes |
| `editorial-infographic` | clean + cool + editorial + dense | Tech explainers, research |
| `fantasy-animation` | organic + vibrant + handwritten + minimal | Educational storytelling |
| `intuition-machine` | clean + cool + technical + dense | Technical docs, academic |
| `pixel-art` | pixel + vibrant + technical + balanced | Gaming, developer talks |
| `scientific` | clean + cool + technical + dense | Biology, chemistry, medical |
| `vector-illustration` | clean + vibrant + humanist + balanced | Creative, children's content |
| `vintage` | paper + warm + editorial + balanced | Historical, heritage |
| `mono` | paper + warm + geometric + minimal | 中文演讲投屏、可编辑 PPTX（原生排版，见 `references/styles/mono.md`） |

### Style Dimensions

| Dimension | Options | Description |
|-----------|---------|-------------|
| **Texture** | clean, grid, organic, pixel, paper | Visual texture and background treatment |
| **Mood** | professional, warm, cool, vibrant, dark, neutral | Color temperature and palette style |
| **Typography** | geometric, humanist, handwritten, editorial, technical | Headline and body text styling |
| **Density** | minimal, balanced, dense | Information density per slide |

Full specs: `references/dimensions/*.md`

### Auto Style Selection

| Content Signals | Preset |
|-----------------|--------|
| tutorial, learn, education, guide, beginner | `sketch-notes` |
| classroom, teaching, school, chalkboard | `chalkboard` |
| architecture, system, data, analysis, technical | `blueprint` |
| creative, children, kids, cute | `vector-illustration` |
| briefing, academic, research, bilingual | `intuition-machine` |
| executive, minimal, clean, simple | `minimal` |
| saas, product, dashboard, metrics | `notion` |
| investor, quarterly, business, corporate | `corporate` |
| launch, marketing, keynote, magazine | `bold-editorial` |
| entertainment, music, gaming, atmospheric | `dark-atmospheric` |
| explainer, journalism, science communication | `editorial-infographic` |
| story, fantasy, animation, magical | `fantasy-animation` |
| gaming, retro, pixel, developer | `pixel-art` |
| biology, chemistry, medical, scientific | `scientific` |
| history, heritage, vintage, expedition | `vintage` |
| lifestyle, wellness, travel, artistic | `watercolor` |
| 中文讲座/分享/闭门会、会议室投屏、要现场改字、单色印刷、mono | `mono` |
| Default | `blueprint` |

## Design Philosophy

Decks designed for **reading and sharing**, not live presentation:
- Each slide self-explanatory without verbal commentary
- Logical flow when scrolling
- All necessary context within each slide
- Optimized for social media sharing

See `references/design-guidelines.md` for:
- Audience-specific principles
- Visual hierarchy
- Content density guidelines
- Color and typography selection
- Font recommendations

See `references/layouts.md` for layout options.

## File Management

### Output Directory

```
slide-deck/{topic-slug}/
├── source-{slug}.{ext}
├── outline.md
├── prompts/
│   └── 01-slide-cover.md, 02-slide-{slug}.md, ...
├── 01-slide-cover.png, 02-slide-{slug}.png, ...
├── {topic-slug}.pptx
└── {topic-slug}.pdf
```

**Slug**: Extract topic (2-4 words, kebab-case). Example: "Introduction to Machine Learning" → `intro-machine-learning`

**Conflict Handling**: See Step 1.3 for existing content detection and user options.

## Language Handling

**Detection Priority**:
1. `--lang` flag (explicit)
2. EXTEND.md `language` setting
3. User's conversation language (input language)
4. Source content language

**Rule**: ALL responses use user's preferred language:
- Questions and confirmations
- Progress reports
- Error messages
- Completion summaries

Technical terms (style names, file paths, code) remain in English.

## Workflow

For the full step-by-step workflow, use `references/workflow.md`. Keep the main
flow in this order:

1. Setup & analyze: load `.lov-skills/lov-any2deck/EXTEND.md` when present, save source content, analyze style signals, detect language, choose slide count, and check for existing `slide-deck/{topic-slug}` output before continuing.
2. Confirm: use `AskUserQuestion` for style, audience, slide count, outline review, and prompt review. If custom dimensions are selected, collect texture, mood, typography, and density.
3. Generate outline: read the selected preset from `references/styles/` or combine dimension docs from `references/dimensions/`, then write `outline.md` using `references/outline-template.md`.
4. Review outline when requested, then generate per-slide prompts under `prompts/` using `references/base-prompt.md` and `references/layouts.md`.
5. Review prompts when requested, generate slide images, optionally apply branding with `scripts/apply-branding.py`, then merge PPTX/PDF with the TypeScript scripts.
6. Report the output directory, generated slide count, PPTX/PDF paths, style, audience, language, and any partial failures.

Partial workflows (`--outline-only`, `--prompts-only`, `--images-only`,
`--regenerate`) and slide modification procedures are documented in
`references/workflow.md`.

## References

| File | Content |
|------|---------|
| `references/analysis-framework.md` | Content analysis for presentations |
| `references/outline-template.md` | Outline structure and format |
| `references/modification-guide.md` | Edit, add, delete slide workflows |
| `references/content-rules.md` | Content and style guidelines |
| `references/design-guidelines.md` | Audience, typography, colors, visual elements |
| `references/layouts.md` | Layout options and selection tips |
| `references/base-prompt.md` | Base prompt for image generation |
| `references/dimensions/*.md` | Dimension specifications (texture, mood, typography, density) |
| `references/dimensions/presets.md` | Preset → dimension mapping |
| `references/styles/<style>.md` | Full style specifications (legacy) |
| `references/config/preferences-schema.md` | EXTEND.md structure |

## Notes

- Image generation: 10-30 seconds per slide
- Auto-retry once on generation failure
- Use stylized alternatives for sensitive public figures
- Maintain style consistency via session ID
- **Step 2 confirmation required** - do not skip (style, audience, slides, outline review, prompt review)
- **Step 4 conditional** - only if user requested outline review in Step 2
- **Step 6 conditional** - only if user requested prompt review in Step 2

## Extension Support

Custom configurations via EXTEND.md. See **Step 1.1** for paths and supported options.

## 维护备注

- `apply-branding.py` 的 `deck_dir` 相对当前 shell cwd 解析；在 `slide-deck/{slug}/` 子目录内调用会拼错路径，统一从仓库根调用（2026-08-21, 4aeebdb）
- branding 合成 2752×1536×20 张大图耗时长（>3 分钟），用后台运行避免超时；PNG 白底二维码需先转 alpha，否则白方块与图纸底色冲突（2026-08-21, 4aeebdb）
- `build-batch.ts` 只识别 `## Illustration N` 标题；自定义大纲用 `## Slide N of M` 时它一张都解析不出，自己写脚本产出 `batch.json` 更快（2026-09-05, f9babe0）
- 讲课版 deck 必须把讲稿写进 `notes/<stem>.md`，画面指令留在 `prompts/`；`merge-to-pptx.ts` 已改为优先取 `notes/` 作演讲者备注，`prompts/` 仅为兜底（2026-09-05, f9babe0）
- 满幅波普/漫画风 deck 不要再叠 logo：`apply-branding.py` 的白底 logo 会与粗描边和网点底冲突，品牌信息直接写进封面画面（2026-09-05, f9babe0）

- mono 风格默认走原生排版：生图只出无文字插画，文字用 python-pptx 排，图片本地转单色调，纸纹与 Logo 进母版；整页生图只在用户明确要求时用（2026-11-27）
- 英文单词标题不要用 Impact（窄体显挤），改用 Arial Black；Georgia 是老式数字，不适合做大数字（2026-11-27）
- AppleScript 让 Keynote 打开 PPTX 是异步的，`open` 返回空值，后台等待也会卡在弹窗上；实机检查交给用户，不抢前台（2026-11-27）

## Runtime context (shared)

运行前读取本 Skill 包的 `skill.yaml`，由宿主提供 `skill-runtime/v1` 上下文。字段解析顺序为：当前请求、项目上下文、个人 Preferences、品牌 Profile、通用默认值。

- 只使用 Manifest 声明的字段；Profile 保存公开品牌事实，Preferences 保存个人工作偏好。
- `required: true` 字段缺失时，按 Manifest 的问题配置向用户提出一个聚焦问题；用户明确同意后再保存回答。
- 报错提供可复制的 `context_id`、字段路径与来源，诊断内容避开秘密、完整私人路径和原始配置。

## 通用反馈闭环

用户在 Skill 驱动任务中提出修改意见时，继续当前产物前必须执行：

1. 先判断意见是 `task-specific`（仅本次）还是 `reusable`（可跨任务复用）。
2. `task-specific` 只修改当前任务，不改 Skill。
3. `reusable` 先确定作用域：领域规则先更新对应 canonical Skill；适用于所有 Skill 的规则先更新共享规范。
4. 完成规则更新、版本、lint 与分发核验后，再把修改应用到当前任务。
5. `reusable` 修改会使此前的“确认”“继续”“发吧”失效；完成当前产物修改和回读后必须停下，等待用户下一步指示，不自动进入发布、提交或其他外部写入。
