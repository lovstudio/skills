# 封面合成 · Cover Composition

![Version](https://img.shields.io/badge/version-0.7.2-CC785C)

微信公众号封面的确定性后期合成模块。它共用同一张艺术背景：横版官方 Logo 保持居中，正方形版和可选的 `3:4` 正文竖向首图把官方 Logo 放在底部中央。

## 默认版式

- 横版 `2.35:1`：Logo 几何居中，最大宽度 `24%`。
- 方版 `1:1`：先从未叠 Logo 的横版背景中心裁切，再把 Logo 放在底部中央；最大宽度 `36%`，最大高度 `15%`，底部边距 `5%`。
- 两个比例都不添加品牌面板、卡片、贴纸或额外文字。
- 正文竖向首图 `3:4`：Logo 底部居中，仅作正文第一块，不代替横版分享封面。
- Logo 资产优先取 `publication.cover_logo`，再回退到 `publication.logo`；配置 `cover_logo_variant: white` 时脚本会验证可见像素确为白色。

## 使用

本模块随父 Skill 安装：

```bash
npx skills add lov-wechat-article-branding -g -y
```

本模块由 `lov-wechat-article-branding-skill` 的 `cover` 或 `full` 管线调用，也可以在需要修正公众号封面双比例 Logo 位置时单独读取。

```text
$lov-wechat-branding-cover-composition 使用官方发布主体 Logo 合成横版和方版封面；正方形版 Logo 按默认规则放在底部。
```

## 验证

检查宽版 Logo 居中、方版与竖版 Logo 底部居中、方版没有残留第二个居中 Logo，并确认所有图使用同一个 `publication.logo` 原文件。上传分享封面时只能选择 `share-cover-wide-logo.jpg`，不能选无 Logo 底图。
