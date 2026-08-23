---
name: lov-bp-deck
description: >
  Turn an approved investor BP outline into a clean, professional slide deck with
  deliberate style selection, real product evidence, charts, branding, PPTX/PDF,
  and a full-deck preview. Use when the narrative already exists and the user wants
  PPT production, visual style exploration, slide regeneration, or export.
  Trigger on "把 BP 大纲做成 PPT", "选择 BP 风格", "生成融资 PPT", "重做第几页",
  "BP deck", "pitch deck design", "render investor slides", or "export BP PDF".
license: MIT
metadata:
  author: contributors
  version: "0.2.0"
  tags: business-plan pitch-deck pptx pdf style charts branding slides
---

# BP Deck

Produce the presentation after the investment narrative is approved. This skill owns
style selection, visual specification, rendering, export, and final-image QA; it does
not invent missing business evidence.

## Input Gate

Required:

- approved `outline.md` or equivalent page-by-page narrative;
- evidence/source notes for core claims;
- project/company name.

Recommended:

- brand logo and primary color;
- real product screenshots;
- founder/team photos;
- source data for charts;
- website/contact destination and QR asset.

If the outline lacks a clear product definition, financing ask, or source-backed core
numbers, stop and recommend `lov-bp-outline` before rendering.

## Output Contract

```text
business-plan/
├── outline.md
├── assets/
├── deck-manifest.md
├── 01-slide-cover.png
├── ...
├── project-bp.pptx
├── project-bp.pdf
└── project-bp-preview.png
```

## Workflow (MANDATORY)

### Step 0: Resolve input and dependency

Resolve this skill directory as `SKILL_DIR` and locate the user's approved outline.
Resolve `lov-any2deck` through the active Agent Skills environment; do not
assume an author's private installation path.

Read `references/user-config.md` and `references/charts-and-visuals.md`.

### Step 1: Lock the narrative

Do not rewrite the storyline during style exploration. Check:

- 12–15 slides unless the user explicitly chooses otherwise;
- one conclusion per slide;
- evidence IDs/source notes on core claims;
- chart type and exact data mapping;
- no placeholder or fabricated metric.

Send evidence blockers back to `bp-outline`. Small copy corrections may be recorded
in `deck-manifest.md` and applied without changing the thesis.

### Step 2: Select style with minimal friction

Infer style from brand, audience, reference images, and the outline. If the user has
not selected a direction, use `AskUserQuestion` once with 2–3 concrete options.

Recommended first option for seed-stage investors:

**Clean editorial** — white/warm-gray background, one brand color, dark conclusion
headlines, real screenshots, consulting-grade charts, and restrained decoration.

Alternative options:

- **Product keynote** — more whitespace and product/demo emphasis;
- **Consulting report** — denser evidence and chart emphasis;
- **Reference-led** — derive a design system from a supplied visual reference.

If the user says “按推荐方案” or “不要问”, use clean editorial.

### Step 3: Write `deck-manifest.md`

Record before rendering:

- outline path and version;
- audience, language, slide count, and presentation duration;
- style name, palette, typography, spacing, and safe margins;
- logos, screenshots, photos, data, and QR assets;
- naming convention;
- expected PPTX/PDF/preview paths;
- any slide intentionally marked illustrative.

### Step 4: Generate with `lov-any2deck`

Invoke `lov-any2deck` using the approved outline and chosen style. Preserve the
BP page order and evidence notes. Use 16:9, body text at least 20 pt, and a single
dominant visual per page.

Prefer:

- real product screenshots and user scenes;
- process diagrams and evidence ladders;
- source-backed charts with axes, units, dates, legends, and notes;
- simple cover and one clear final contact action.

Avoid stock-photo filler, decorative card walls, gradients, tiny source text, fake
dashboards, and unsourced growth curves.

### Step 5: Export and inspect

Produce editable PPTX, PDF, all slide images, and one full-deck preview. Review every
page at presentation size:

- no clipped/overlapping text or broken CJK;
- title/body/source hierarchy is consistent;
- logos are optically balanced;
- images are not stretched;
- chart values match the evidence ledger;
- product screenshots are genuine and legible;
- QR codes decode from the final rendered slide;
- PPTX and PDF page counts match;
- filenames include project, document type, and date/version.

Regenerate only affected slides. Record the result in `deck-manifest.md`.

### Step 6: Handoff

Return PPTX, PDF, preview, manifest, and any unresolved visual risks. Recommend
`lov-bp-polish` for an adversarial final review.

## Recommended Next Step

```text
$lov-bp-polish ./business-plan/project-bp.pdf --full
```

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
