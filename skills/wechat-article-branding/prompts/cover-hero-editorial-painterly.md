# 微信公众号艺术封面 Prompt 模板

这是 branding skill 的可复用封面生产 Prompt。它负责生成“艺术图片打底”，随后由
`cover-composition` 读取官方发布主体 Logo，完成横版居中、方版底部居中、底部调暗和双比例输出。

## Resolved direction

```yaml
source_skill: baoyu-cover-image
type: hero
style: editorial
palette: elegant
rendering: painterly
text: none
mood: balanced
center_safe_zone: true
square_bottom_logo_safe_zone: true
wide_aspect: 2.35:1
square_aspect: 1:1
```

## Production prompt

在提交给图像生成器前，将双大括号字段替换为当前文章的真实命题；保留所有构图、材质和
负面约束。`text: none` 是艺术底图约束，官方 Logo 必须在生成后作为独立品牌层叠加。

```text
Editorial hero artwork for a thoughtful WeChat article about {{ARTICLE_THESIS}}. Build one
clear visual metaphor for {{CORE_RELATIONSHIP}}, rather than a collection of decorative
objects. Arrange {{PRIMARY_FORMS}} across a wide cream paper field, with a low-detail,
quietly contrasting safe zone at the exact center for a post-composited publisher Logo.
Keep the lower-center band of the center 1:1 crop calm enough for a bottom-centered square Logo.
Use {{MATERIAL_LANGUAGE}}, painterly gouache and screen-print texture, layered paper grain,
restrained independent-creator magazine art direction, an elegant palette of {{PALETTE}},
balanced asymmetry, generous negative space, and a calm intelligent mood. The composition
must read clearly at 2.35:1 and retain its central visual logic when cropped to 1:1.

No title, no letters, no numbers, no pseudo-text, no logo, no watermark, no UI, no people,
no stock photography, no generic warm desk still life, no stationery flat lay, no product
mockup, no templated tech particles, no neon, no clutter, no separate text panel.
```

## Filled direction example

下面的实例用于校准生成方向，不限制文章主题：

```text
Editorial hero artwork for a thoughtful article about pricing creative AI Skills. Three
sculptural abstract forms stand across a wide cream paper field: a coral-red arch on the
left, a muted teal form in the middle, and a deep ink-blue form on the right. A thin brass
thread passes through all three forms and hangs in a gentle curve, expressing time cost,
value assessment, and pricing as one connected model. Painterly gouache and screen-print
texture, layered paper grain, restrained independent-creator magazine art direction,
elegant coral, teal, ink blue, cream, dusty mauve, and brass palette, generous low-detail
negative space at the exact center for a post-composited publisher Logo, balanced asymmetry,
and a calm lower-center band inside the square crop for its bottom-centered Logo,
quiet intelligence.

No title, no letters, no numbers, no pseudo-text, no logo, no watermark, no UI, no people,
no stock photography, no warm desk still life, no card mockup, no gradients, no neon, no
clutter.
```

## Post-production contract

- 先将艺术底图铺满 `2.35:1` 宽版画布并完成调暗，再从尚未叠加 Logo 的宽版背景中心派生 `1:1` 方版。
- 底部从约 38% 画面高度开始做轻微渐变调暗，默认强度为 `0.45`。
- 读取 `publication.logo`，保持原始字形、比例、透明区域和颜色；横版 Logo 几何中心与画布中心重合，默认最大宽度为画布宽度的 `24%`。
- 方版单独合成同一 Logo，默认底部居中，最大宽度 `36%`、最大高度 `15%`、底部边距 `5%`。
- 两个比例都不添加面板、卡片、贴纸、胶囊底或额外品牌文字。
- 保存底图、宽版合成图、方版合成图、上传用 JPG，以及本次替换字段后的完整 Prompt。
