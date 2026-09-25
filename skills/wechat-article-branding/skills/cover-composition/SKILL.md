---
name: lov-wechat-branding-cover-composition
description: >
  按确定性规则合成公众号品牌封面：共用艺术底图与底部调暗，横版官方 Logo 居中，正方形版与可选竖向正文首图的 Logo 默认置于底部中央。Use when a WeChat cover needs repeatable wide, square, and vertical Logo composition.
license: MIT
compatibility: "Embedded module; deterministic compositor requires Python 3.10+ and Pillow, or an equivalent existing local WeChat cover editor."
metadata:
  author: contributors
  version: "0.7.2"
  tags:
    - cover-composition
    - dual-ratio-logo-layout
    - wechat
  dependencies: []
---

# 封面合成 · Cover Composition

本模块负责封面的最终确定性合成，不负责生成新的 Logo，也不决定正文是否启用首屏。默认版式是“横版居中，方版底部居中”；父管线启用正文首屏时，额外合成 `3:4` 竖向版并将 Logo 放在底部安全区。

## Triggers

### Activate when

- `cover-direction` 已产出公众号分享封面的艺术底图，需要叠加发布主体 Logo 并输出双比例制品。
- 用户要求复用艺术图片打底的既有封面风格，或指定横版与方版不同的 Logo 位置。
- Branding 管线启用分享封面制作或重构。
- The user asks to "center the Logo on the wide cover and place it at the bottom of the square cover".

### Do not activate when

- 当前请求只需要正文首屏品牌图，不需要分享封面。
- 当前请求只做封面审计，不允许生成或合成新制品。

## Composition contract

1. 使用 `cover-direction` 产出的艺术主图作为底图；先铺满 `2.35:1` 画布，再处理品牌层。
2. 按 `wechat_article_branding.cover_composition.background_dimming` 添加从约 38% 画面高度开始的底部渐变调暗，默认强度为 `0.45`。
3. 优先读取 `publication.cover_logo`，字段缺失时才回退到 `publication.logo`；保留原始字形、比例、透明区域和颜色。若 `publication.cover_logo_variant` 为 `white`，合成前必须验证可见 Logo 像素为低色差高亮度白色，不得回退为橙色。宽版 Logo 默认最大宽度为画布宽度的 `24%`、最大高度为画布高度的 `45%`，以画布几何中心定位。
4. 从完成调暗、但尚未叠加 Logo 的宽版背景中心裁切 `1:1`。不要从已经带有居中 Logo 的宽版成品裁方图，否则方版会错误继承横版位置。
5. 在方版背景上单独叠加同一官方 Logo，默认 `position: bottom_center`、最大宽度 `36%`、最大高度 `15%`、底部边距 `5%`。用户显式指定方版位置或尺寸时，以当前请求为准。
6. 两个比例都不要加左下角面板、圆角卡片、贴纸、胶囊底或额外品牌文字。
7. 输出未叠加 Logo 的艺术底图、宽版合成图、方版合成图以及上传用 JPG；保留合成前后的本地文件便于回滚和比较。
8. 父管线启用 `opening_hero` 时，从同一艺术世界制作 `3:4` 竖向版，Logo 默认底部居中、最大宽度 `42%`、底部边距 `8%`。该文件仅作正文首屏，不替代分享封面上传件。
9. 文件角色必须明确命名：`share-cover-wide-logo.*`、`share-cover-square-logo.*`、`opening-hero-vertical-logo.*`。禁止上传名为 `background` 或未经 Logo 验收的艺术底图。

## Deterministic compositor

```bash
python3 "$SKILL_DIR/scripts/compose_cover.py" \
  --background ARTWORK \
  --logo PUBLICATION_LOGO \
  --logo-variant white \
  --output-dir OUTPUT_DIR \
  --opening-hero
```

脚本会输出 PNG、上传用 JPG 和 `cover-composition.json`。回执记录 Logo 源文件 SHA-256、变体、可见像素平均 RGB、各产物尺寸与 Logo 像素包围盒；如 Logo 缺失、没有可见 alpha/色彩像素、声明 `white` 但像素不是白色，或产物与无 Logo 背景一致，则立即失败。

## Existing editor compatibility

如果当前环境可用旧的公众号封面裁切器，可以复用其底图铺满、渐变调暗和 Logo 覆盖能力，但需要支持双位置合成。横版定位为 `((画布宽度 - Logo 宽度) / 2, (画布高度 - Logo 高度) / 2)`；方版定位为 `((方版宽度 - Logo 宽度) / 2, 方版高度 - 底部边距 - Logo 高度)`。裁切发生在方版 Logo 合成之前。

## Validation

- 宽版 Logo 的几何中心与画布中心一致；方版 Logo 水平居中并位于底部安全区。
- 方版背景来自未叠 Logo 的宽版背景中心裁切，不得残留第二个居中 Logo。
- Logo 来自解析后的 `publication.cover_logo` 或其明确回退 `publication.logo`，没有被图像模型重画或变形。
- 存在 `publication.cover_logo` 时，收据必须指向该文件而不是通用 `publication.logo`；声明 `white` 时，Logo 可见像素必须通过白色验证。
- 宽版上传件与无 Logo 底图在记录的 Logo 包围盒内存在像素差异；收据中 Logo 源文件 SHA-256 与 `publication.logo` 一致。
- 启用竖向首图时，产物为 `3:4`、Logo 位于底部安全区，且这张图不被误用为分享封面。
- 两个比例均只有一个主视觉焦点，且没有品牌面板遮挡艺术主体。
- 上传前先查看宽版和中心方形裁切；上传后检查平台 CDN 成品。

## Runtime context (shared)

运行前读取本 Skill 包的 `skill.yaml`，由宿主提供 `skill-runtime/v1` 上下文。字段解析顺序为：当前请求、项目上下文、个人 Preferences、品牌 Profile、通用默认值。

- 只使用 Manifest 声明的字段；Profile 保存公开品牌事实，Preferences 保存个人工作偏好。
- `required: true` 字段缺失时，按 Manifest 的问题配置向用户提出一个聚焦问题；用户明确同意后再保存回答。
- 报错提供可复制的 `context_id`、字段路径与来源，诊断内容避开秘密、完整私人路径和原始配置。
