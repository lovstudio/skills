---
name: lov-cover-package
description: >
  从文章命题生成无文字艺术底图，并用官方 Logo 确定性合成 2.35:1 公众号分享封面与独立的 4:3 横向正文首图。Use when the user asks for“双尺寸封面”“cover package”或“wide cover and 4:3 body hero”。
license: MIT
compatibility: "Embedded module of lov-article-creator; Pillow 10+; host image generation or a supplied art master."
depends_on:
  - lov-branding-consistency
metadata:
  author: LovStudio
  version: "0.3.1"
  tags: [wechat-cover, branding, image-composition]
  dependencies: []
---

# Cover Package

为同一篇文章生成视觉语言一致、但角色和构图独立的分享封面与 `4:3` 正文首图。生图或合法素材负责艺术底图，脚本负责 Logo、比例、导出与校验。

## Triggers

### Activate when

- “给这篇公众号文章做分享封面和 4:3 正文首图。”
- “沿用品牌系统生成一套双尺寸视觉包。”
- “Create a wide WeChat cover and a 4:3 body opening image.”

### Do not activate when

- 只要文章正文；交给 `lov-article-writing`。
- 只有旧成品需要检查；交给 `lov-quality-gate`。
- 用户只要一张不属于文章体系的独立海报；使用通用图像能力。

## Composition contract

本模块吸收 `lov-wechat-branding-cover-composition` 的中心横版构图、底部渐暗和官方 Logo 后合成原则；正文首图遵循公众号出版规范，固定为独立的 `4:3` 横向资产。

- 横版：默认 `1880×800`，比例 `2.35:1`，Logo 居中。
- 正文首图：默认 `1600×1200`，比例 `4:3`，Logo 位于底部安全区。
- 两张图使用同一艺术世界，但不能把一张成品直接拉伸成另一张。
- 底图禁止标题、字母、数字、Logo、水印和伪文字。
- Logo 只使用 Profile 中的发布主体官方白色横向 raster lockup；母品牌 Logo、方形图标和橙色变体不得替代，生图模型不得重画。

## Workflow

1. 读取 Kit 根目录 `references/cover-system.md` 与 `prompts/cover-art.md`。
2. 从文章核心判断提取一个主视觉隐喻，明确中心焦点、留白、安全区和禁用项。
3. 使用宿主图像生成能力，或接收用户提供的合法艺术底图；生成后先做无字、无标、无水印检查。
4. 从未叠 Logo 的底图分别为分享封面和正文首图 crop/reframe；共享视觉语言，不复用分享封面成品。
5. 运行 Kit 根目录 `scripts/compose_covers.py`，用发布主体官方白色横向 Logo 确定性合成 PNG/JPG；内容宽高比小于 `1.8` 或白色像素比例小于 `0.98` 时必须停止。
6. 回读两张成品，确认主体、Logo、裁切和移动端观感，再交给质量门。

## Acceptance

- 输出 master、两套 PNG/JPG 和 `cover-manifest.json`。
- 分享封面与正文首图尺寸、比例、Logo 位置和散列值可回读。
- 文章标题缩略图下仍有一个清晰主焦点。
- `4:3` 正文首图不是分享封面的机械拉伸，底部 Logo 不贴边、不变形。
- 不出现错误发布主体、母品牌 Logo、方形 Logo、橙色 Logo、AI 伪 Logo 或无关产品标识。

## Dependencies

Pillow 10+ and either host image generation or a supplied legal art master.
