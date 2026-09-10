---
name: lov-mobile-infographic
description: >
  把结论、研究或对话整理成适合手机竖屏阅读的证据型信息图，输出可编辑 HTML 与 1080 宽 2× PNG 卡片系列；
  适用于“把这个内容做成手机能读的信息图”“做一组竖版信息图”
  和 "turn this into a mobile infographic"。
license: MIT
compatibility: >
  Portable Agent Skills format. Python 3.8+; PNG rendering requires Playwright
  for Python with Chromium or Google Chrome. Generated HTML is portable and
  embeds the resolved brand logo as a data URL.
depends_on:
  - lov-branding-consistency
metadata:
  author: skill-publisher
  version: "0.1.0"
  card_standard: lovstudio/skill-card/v1
  content_class: microcopy
  tags:
    - mobile
    - infographic
    - card-series
    - readability
    - html
    - png
---

# 手机信息图 · Mobile Infographic

把一段已经有结论的内容，重排成手机上真的读得下去的证据型信息卡：单列阅读路径、
明确的字号下限、可核查的口径与来源，以及能从一张扩展到一组的系列结构。

这不是把咨询 Exhibit 缩小，也不是把整卡交给生图模型。文字、证据和排版全部由 DOM 生成，
PNG 由浏览器精确栅格化，交付时同时给出可编辑 `card.html` 与 2× PNG。

## Triggers

### Activate when

- 用户说“把上面这段做成手机能看的卡片”“做一组适合手机阅读的竖版信息图”“这段总结发朋友圈或小红书”。
- 用户要一张或一组竖屏信息卡，用于手机信息流、朋友圈、微信图文、小红书笔记或课程补充材料。
- The user asks to "turn this into a mobile infographic", "make a vertical infographic for phones",
  or "export a readable card series as PNG".

### Do not activate when

- 用户要的是 16:9 桌面阅读的咨询 Exhibit、指标矩阵或投资阶梯；交给 `lov-professional-infographic`。
- 用户要的是带独立插图的图鉴或收藏卡，或需要可复制生图 Prompt 的系列卡；交给 `lov-gen-card`。
- 用户要的是营销种草视觉图卡（多种卡通风格、生图渲染）；交给 `baoyu-xhs-images`。
- 用户要的是产品宣发海报或一页产品故事；交给 `lov-product-onepage`。
- 用户只要文字总结、幻灯片或文档排版；本 Skill 不替代写作、演示与文档能力。

## User Profile (cross-session)

Every generated Skill is connected to the shared `user-profile/v1` contract in
`skill.yaml`. Read the shared user, brand, workspace, preferences, and this
Skill's `skills.<skill_id>` namespace at the start of every run. Keep the source
portable: resolved personal values belong in the shared profile, never here.

When the user directly states a durable preference or brand fact, persist it
through `scripts/profile_store.py` and report the saved profile path. Put
Skill-specific values under `records.<field>`; use `brand.<field>` or
`user.<field>` for shared values. Do not persist inferred secrets or credentials.
See `references/user-profile.md` for the complete contract.

品牌解析顺序见 [`references/user-config.md`](references/user-config.md)。

## Skill Group Composition

Read `references/skill-composition.md` before deciding whether to invoke or
extend any adjacent capability. The record distinguishes optional upstream and
downstream handoffs from embedded Kit modules. Do not silently depend on a
sibling Skill that is not shipped with this source.

## Required references

Read before authoring:

1. `references/mobile-reading-standard.md` — 字号下限、行宽、对比度、安全区、比例与一屏信息量。
2. `references/template-grammar.md` — 六个语义模板的适用关系与选择规则。
3. `references/spec-schema.md` — HTML `data-*` 契约与 audit 字段。

Read `references/series-and-export.md` when the output is a series, a long image,
or platform-specific delivery.

## Workflow (MANDATORY)

**You MUST follow these steps in order.**

### Step 0: Resolve skill root, dependencies, and runtime context

- Use `SKILL_DIR` if the environment provides it.
- Otherwise infer the installed skill directory from the current skill context.
- Verify `scripts/infographic_cli.py`, `assets/card-base.css`, `assets/templates/`, and
  the required references exist before work.
- Resolve `context.profile` on every invocation. The precedence is current request,
  project context, Skill-specific profile records, shared preferences, shared
  brand/user profile, then safe defaults.

```bash
export SKILL_DIR="/path/to/lov-mobile-infographic"
python3 "$SKILL_DIR/scripts/infographic_cli.py" --help
```

### Step 1: Preserve and scope the source

- If the user says “以上内容”“刚才那段”“this result”, use the current conversation result.
  Do not ask them to paste it again.
- Keep the exact input in `source.md` under an `Exact input` section. Append normalized
  notes and calculations below it; never replace the supplied material.
- Decide the reader and the use moment: 信息流预览、朋友圈九宫格、微信图文内嵌、课程补充。
- Keep one argument per card; split genuinely separate stories into a series
  (see `references/series-and-export.md`).

### Step 2: Build the evidence table before the visual

Write `brief.md` from the scaffold, then fill the evidence table:

| ID | 论点 / 判据 | 精确证据 | 编码方式 | 直接标注 |
| --- | --- | --- | --- | --- |

For every visible mark record the source and location, unit, denominator, period,
and whether it is fact, estimate, assumption, or interpretation. Never invent a
proxy value or a score.

### Step 3: Choose one template and the ratio

Pick exactly one template from `references/template-grammar.md`. Default ratio is
`3:4`; use `4:5` for feeds, `9:16` for full-screen story, `1:1` for grid tiles,
and `long` only when one argument genuinely needs more height.

### Step 4: Scaffold

```bash
python3 "$SKILL_DIR/scripts/infographic_cli.py" scaffold \
  --template single-claim \
  --ratio 3:4 \
  --filename card-01.html \
  --series-index 1 --series-size 3 \
  --eyebrow "运营手册 · 01" \
  --title "优化 harness 的三步" \
  --claim "模型是自变量，harness 是因变量" \
  --source "来源：…" \
  --output-dir "<project directory>"
```

The template is a semantic skeleton. Every element carrying `data-skeleton`
still holds placeholder copy.

### Step 5: Author the card

- Replace every `data-skeleton` element and remove the attribute once the copy is final.
- Keep exactly one `data-claim` element per card: the single conclusion this card argues.
- Attach evidence with `data-source-ref`; declare visual variables with `data-encoding`;
  mark decision-changing evidence with `data-annotation`.
- Write units next to values, put the caveat next to the number it qualifies, and keep
  the source line readable but subordinate.
- Do not add a second conclusion, a wall of similar boxes, or decorative imagery.
- Keep the brand footer: logo, attribution, and `n/N` page mark.

### Step 6: Render

```bash
python3 "$SKILL_DIR/scripts/infographic_cli.py" render \
  --input "<project>/card-01.html" \
  --output "<project>/card-01.png" \
  --scale 2
```

The renderer captures the `[data-card]` element at an exact pixel size and fails
when the PNG dimensions do not match the canvas.

### Step 7: Audit and review

```bash
python3 "$SKILL_DIR/scripts/infographic_cli.py" audit \
  --input "<project>/card-01.html" \
  --image "<project>/card-01.png" \
  --report "<project>/card-01.audit.json" \
  --ratio 3:4
```

The audit measures the rendered page in a real browser: font floors, characters per line,
contrast, overflow, out-of-canvas elements, safe area, single claim, evidence linkage,
brand footer, series page mark, remaining skeleton copy, and truncation. It writes a
100-point proxy with an 85 threshold and critical-dimension floors.

Then inspect the PNG at original detail **and** at thumbnail size (a 320px-wide downscale
is enough). Answer:

1. 5 秒内能否说出这张卡在讲什么？
2. 阅读顺序是否从标题到结论再到依据与来源？
3. 有没有被省略号截断、被裁切或压线的文字？
4. 每个数字是否带单位与口径？
5. 有没有大片空白或被撑满到窒息的区块？

Record the reviewed image and the concrete finding, then run the release gate:

```bash
python3 "$SKILL_DIR/scripts/infographic_cli.py" audit \
  --input "<project>/card-01.html" \
  --image "<project>/card-01.png" \
  --report "<project>/card-01.audit.json" \
  --ratio 3:4 \
  --human-review passed \
  --review-note "<what was verified at full size and thumbnail size>" \
  --strict
```

`passed` without both `--image` and a specific review note is invalid. Do not report success
because `audit.json` shows zero machine errors — the machine proxy is not proof of readability.

### Step 8: Series and export

For a series, scaffold each card with the same `--series-size`, write `manifest.json` from the
case template, and verify that every card keeps the same width, safe area, and footer position.
See `references/series-and-export.md`.

### Step 9: Deliver

Return clickable paths to the PNG files, the editable HTML, `brief.md`, `source.md`,
`audit.json`, and `manifest.json` for a series. State the template, ratio, evidence mode,
proxy score, and human-review result. Disclose assumptions, omitted material, and any card
that is still machine-only verified.

## Dependencies

- Python 3.8+ standard library.
- Playwright for Python plus Chromium or Google Chrome for `render` and `audit`:

```bash
python3 -m pip install "playwright>=1.45,<2"
python3 -m playwright install chromium
```

- `scaffold` and `init-brand` need no browser and no network.
- Brand assets stay user-configurable; the packaged default is a placeholder profile,
  not a claim about the user's brand.

## CLI

```bash
python3 "$SKILL_DIR/scripts/infographic_cli.py" --help
python3 "$SKILL_DIR/scripts/infographic_cli.py" init-brand --help
python3 "$SKILL_DIR/scripts/infographic_cli.py" scaffold --help
python3 "$SKILL_DIR/scripts/infographic_cli.py" render --help
python3 "$SKILL_DIR/scripts/infographic_cli.py" audit --help
python3 "$SKILL_DIR/scripts/test_infographic_cli.py"
```

## 通用反馈闭环

用户在 Skill 驱动任务中提出修改意见时，继续当前产物前必须执行：

1. 先判断意见是 `task-specific`（仅本次）还是 `reusable`（可跨任务复用）。
2. `task-specific` 只修改当前任务，不改 Skill。
3. `reusable` 先确定作用域：领域规则先更新对应 canonical Skill；适用于所有 Skill 的规则先更新共享规范。
4. 完成规则更新、版本、lint 与分发核验后，再把修改应用到当前任务。
5. `reusable` 修改会使此前的“确认”“继续”“发吧”失效；完成当前产物修改和回读后必须停下，等待用户下一步指示，不自动进入发布、提交或其他外部写入。
