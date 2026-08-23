---
name: lov-bp-polish
description: >
  Review and improve an existing BP outline, PPTX, PDF, or rendered slide set across
  investment logic, evidence, copy, charts, and visual quality. Produces a scored
  report, page-level revisions, and targeted regeneration instructions while keeping
  facts separate from assumptions. Trigger on "润色 BP", "审稿商业计划书", "PPT 不专业",
  "逐页检查", "改图表", "BP review", "polish pitch deck", or "audit investor deck".
license: MIT
metadata:
  author: contributors
  version: "0.2.0"
  tags: business-plan review polish audit evidence charts visual-quality pitch-deck
---

# BP Polish

Improve an existing BP without silently changing its business facts. This skill can
be used before deck production, after rendering, or in a correction loop.

## Modes

| Mode | Input | Focus |
|---|---|---|
| `content` | Outline / Markdown | Product definition, story, copy, page rhythm |
| `evidence` | Outline + ledger/sources | Claims, metrics, TAM/SAM/SOM, assumptions |
| `visual` | PPTX/PDF/slide images | Hierarchy, charts, layout, branding, QR codes |
| `full` | Any complete BP workspace | All dimensions + correction loop |

Infer the smallest useful mode from the request. Do not require a PDF when the user
only wants the outline reviewed.

## Output Contract

```text
business-plan/
├── reports/bp-review.md
├── outline.md                 # patched only when authorized by the request
├── deck-manifest.md           # updated for visual fixes
└── revised slide/deck assets  # only affected artifacts
```

## Workflow (MANDATORY)

### Step 0: Resolve source and mode

Resolve this `SKILL.md` directory as `SKILL_DIR`. Inspect the supplied source and any
existing BP workspace. Reuse audience, stage, style, and evidence definitions.

If multiple review modes are plausible, prefill from the user's wording. Ask one
compact question only when the choice materially changes the work. “不专业” defaults
to `full`; “文字太技术” defaults to `content`; “图表不好看” defaults to `visual`.

Read `references/review-rubric.md`, `references/charts-and-visuals.md`, and
`references/user-config.md` as relevant.

### Step 1: Run deterministic outline audit

When an outline exists:

```bash
python3 "$SKILL_DIR/scripts/audit_bp.py" \
  --input ./business-plan/outline.md \
  --output ./business-plan/reports/bp-review.md
```

Use `--strict` before final delivery. The script checks structure and evidence
hygiene; it does not replace investor judgment or visual inspection.

### Step 2: Review as four adversaries

1. **Non-technical investor** — can the product be repeated after ten seconds?
2. **Category expert** — which product/competition claims are naive or imprecise?
3. **Skeptical partner** — which core claims lack proof or overstate traction?
4. **Design director** — where does layout reduce trust or distort meaning?

For every issue record slide, severity, why it matters, and exact revision.

### Step 3: Protect facts during polishing

- Never make numbers “look better”.
- Never turn an assumption into a fact.
- Never invent a customer quote or testimonial.
- Never widen TAM without a buyer and price bridge.
- Never change a product boundary solely to improve the story.

If a revision needs new evidence, mark an evidence blocker and return it to
`lov-bp-outline`.

### Step 4: Inspect rendered slides

For visual/full mode, create or inspect a contact sheet and every page at normal
presentation size. Check:

- one conclusion per page;
- body text at least 20 pt;
- optical alignment and whitespace;
- chart axes, units, legends, dates, and sources;
- genuine, legible product screenshots;
- unstretched images and logos;
- no clipped text or broken CJK;
- QR codes decoded from final rendered pages;
- clean cover and one-action final page;
- matching PPTX/PDF page counts and normalized filenames.

### Step 5: Apply targeted fixes

Classify each fix:

- **copy fix** — patch outline and regenerate affected slides;
- **evidence blocker** — update ledger/source before rewriting;
- **visual defect** — change layout/style or regenerate affected slides only.

Do not regenerate the whole deck for a one-page issue. Repeat audit → fix → audit for
at most three cycles.

### Step 6: Deliver the report

Lead with verdict and score, then blockers, page-level findings, evidence gaps,
visual QA, and delivery status. Use `assets/templates/bp-review.md`.

Target: 85+ with no blocker. A high numeric score never overrides fabricated data,
missing financing ask, broken source, unreadable slide, or invalid QR code.

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
