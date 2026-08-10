# 输入与交付契约

## 输入

### Markdown

使用 CommonMark/Pandoc Markdown。图片使用标准 Markdown；视频、音频和嵌入内容使用原生 HTML。建议每个媒体都有标题、说明、替代文字和可访问链接。

```markdown
![产品演示封面](https://example.com/assets/demo-poster.jpg)

<video controls src="https://example.com/assets/demo.mp4" poster="https://example.com/assets/demo-poster.jpg">
  产品演示视频。
</video>

<audio controls src="assets/interview.mp3">访谈音频。</audio>
```

### `rich-export.json`

适合产品直接输出。`document` 是唯一可以用于成品元数据的来源；`content.markdown` 是用户可见正文；`media` 只通过 `{{media:ID}}` 插入正文。

```json
{
  "version": 1,
  "document": { "title": "发布说明", "author": "", "lang": "zh-CN" },
  "content": { "markdown": "# 发布说明\n\n{{media:demo}}" },
  "media": [
    {
      "id": "demo",
      "kind": "video",
      "src": "assets/demo.mp4",
      "poster": "assets/demo-poster.jpg",
      "title": "产品演示",
      "caption": "两分钟了解核心流程",
      "transcript_url": "assets/demo-transcript.md"
    }
  ]
}
```

`kind` 支持 `image`、`video`、`audio`、`iframe`；`src` 必填，`poster`、`title`、`caption`、`transcript_url` 推荐填写。未被正文引用的媒体不会自动加入成品。

### HTML

输入 HTML 时，脚本将其规范化为 Markdown 后生成各格式。因此适用于以语义内容为主的页面；若必须保留一个复杂 Web 应用的完整交互，产品应直接交付 HTML 文件夹，再使用该页面的打印样式生成 PDF。

## 输出布局

```text
OUT/
  source.md
  html-single/DOCUMENT.html
  html/DOCUMENT/index.html
  html/DOCUMENT/assets/
  docx/DOCUMENT.docx
  pdf/DOCUMENT.pdf
  export-manifest.json
  DOCUMENT-export.zip            # 仅 --zip
```

`export-manifest.json` 记录源、格式、文件、警告与媒体投影，方便产品在下载中心展示状态、校验文件及复跑失败任务。

## 静态投影

| HTML 元素 | HTML | Markdown/DOCX/PDF |
|---|---|---|
| 图片 | 图片 | 嵌入图片 |
| video | 可播放 | 封面（如有）+ 标题/说明 + 视频链接 + 字幕/文字稿链接 |
| audio | 可播放 | 标题/说明 + 音频链接 + 文字稿链接 |
| iframe | 可交互 | 标题/说明 + 原页面链接 |

静态投影的目的不是复制播放器，而是确保读者在不能播放的介质里仍知道媒体是什么、为何相关及如何访问。
