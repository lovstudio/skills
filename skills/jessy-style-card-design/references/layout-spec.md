# 版式 spec（render_card.py 的输入）

一份 JSON 描述一张名片。每面是一组绝对定位的块，渲染器把所有素材内嵌成 data URI，
写出自包含 HTML，在 headless Chrome 里检查版式，再截图。素材路径相对 spec 文件。

## 顶层字段

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| `canvas.width` / `canvas.height` | 是 | CSS 像素。横版 1080×648，竖版 648×1080 |
| `canvas.scale` | 否 | 截图倍率，默认 3 |
| `canvas.mm` | 否 | 实物尺寸备注，例如 `[90, 54]`，渲染器不使用 |
| `theme` | 否 | 颜色与字体 token，见下 |
| `front` / `back` | 至少一个 | 每面 `background`（token 或颜色）与 `blocks` |
| `stack_gap` | 否 | 正反拼图中间的间距像素，默认 0 |
| `output.stem` | 否 | 文件名前缀；命令行 `--stem` 优先 |
| `output.labels` | 否 | 三张图的文件名标签，默认 正面 / 背面 / 正反 |
| `title`、`lang` | 否 | HTML 标题与语言 |
| `extra_css` | 否 | 追加样式，例如给 `html` 文本里的 span 定字距 |

## theme

默认 token：`accent`、`paper`、`ink`、`ink2`、`ink3`、`on_accent`、`font_sans`、`font_serif`、`font_mono`。
可以新增任意小写 token，例如 `"gold": "#B8925A"`。块里凡是颜色字段都可以写 token 名或 CSS 颜色；
字体字段写 `sans`、`serif`、`mono` 或字体族字符串。

## 通用定位字段

所有块都支持：`left`、`top`、`right`、`bottom`、`width`、`height`（数字是像素，也可写 `"50%"`、`"auto"`），
`center`（`x`、`y`、`xy`，没写对应边时自动放到 50%），`opacity`、`z`、`id`，以及：

- `decor: true`：装饰层，不参与重叠检查（插画、铺底色块、分隔线）。
- `bleed: true`：允许超出画布（出血装饰）。

## 文字字段

`size`、`weight`、`color`、`font`、`tracking`（em）、`line_height`、`align`、`italic`、
`optical_center`（居中文字补偿末尾字距）。

## 块类型

### name

`text`（或 `html`）、`latin`、`gap`；主名用文字字段，英文名用加 `latin_` 前缀的同名字段
（`latin_size`、`latin_color`、`latin_weight`、`latin_font`）。两者基线对齐。

### text

`text`（`\n` 换行，自动转义）或 `html`（原样输出，只写自己需要的 span）。默认不换行；
需要自动换行时写 `wrap: true` 和 `width`，溢出会被检查器报出。

### contacts

一列带图标的联系行。

| 字段 | 默认 | 说明 |
| --- | --- | --- |
| `items` | 必填 | 每项 `icon` + `text`；或 `label` + `text`（label 用次级颜色）；或 `lines` 多行 |
| `icon_style` | `tile` | `tile` 圆角方块、`circle` 圆形、`plain` 无底 |
| `tile_size` / `tile_radius` | 32 / 4 | 图标底块大小与圆角 |
| `icon_size` / `stroke` | 18 / 1.9 | 图标大小与描边 |
| `tile_color` / `icon_color` | accent / on_accent | `plain` 时图标默认 accent |
| `icon_gap` / `row_gap` | 20 / 26 | 图标与文字、行与行的间距 |
| `label_gap` / `label_color` | 10 / ink3 | label 后的间距与颜色 |
| `prefix_gap` / `prefix_color` | 14 / 继承 | `lines` 里 `[前缀, 正文]` 的前缀样式 |

`lines` 的元素可以是字符串，也可以是 `["上海", "陆家嘴数智港"]` 这样的前缀对。
内置图标（Lucide，ISC）：`phone`、`smartphone`、`mail`、`at-sign`、`globe`、`link`、`map-pin`、
`book-open`、`message-circle`、`building`、`briefcase`、`user`；别名 `pin`、`book`、`web`、`wechat`、
`email`、`address`、`company`、`mobile`。需要别的图标时用 `icon_svg` 写 24×24 描边 SVG 的内部标记。

### image

`src`、`alt`、`fit`。Logo 写 `height` 或 `width` 之一保持比例。装饰插画加 `decor`，出血加 `bleed`。

### qr

`src`、`size`（默认 150）、`pad`（白边，默认 8）、`bg`、`caption`，说明文字用 `caption_` 前缀字段
（`caption_size`、`caption_color`、`caption_tracking`、`caption_gap`）。

### rect

`color`、`radius`，用于色条、分隔线、色块；铺底时加 `decor`。

## 命令

```bash
python3 scripts/render_card.py card.json --out-dir OUT --version v0.1 \
  [--stem 前缀] [--date 2026-11-18] [--sides front,back,stack] [--scale 3] [--html-only] [--force]
```

输出 `前缀-正面-日期-版本.png`、`前缀-背面-…`、`前缀-正反-…` 与 `前缀-日期-版本.html`，
标准输出是 JSON 报告：每张图的像素与字节、版式问题列表。

## 版式检查

渲染前在 Chrome 里量每个块的实际位置：

- `out-of-bounds`：非 `bleed` 块超出画布。
- `overlap`：两个非 `decor` 块重叠超过 1 px。
- `text-overflow`：定宽文字块内容溢出。

有问题时仍然出图，退出码为 3。改 spec 后加 `--force` 重渲染。
