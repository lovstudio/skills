# lovstudio-bp-deck

![Version](https://img.shields.io/badge/version-0.1.0-CC785C)

把已经确认的 BP 大纲做成专业 PPTX、PDF 和全稿预览。

## 安装

```bash
npx lovstudio skills add bp-deck -g -y
```

依赖免费的 `lovstudio-any2deck`。

## 使用

```text
$lovstudio-bp-deck ./business-plan/outline.md
$lovstudio-bp-deck ./outline.md --style minimal
$lovstudio-bp-deck 重做第 6 和第 12 页，保持其他页面不变
```

## 交付物

- PPTX
- PDF
- 全部页面图片
- 全稿预览
- `deck-manifest.md`

## License

MIT
