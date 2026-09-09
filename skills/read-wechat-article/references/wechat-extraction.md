# 公众号文章提取与整理说明

## 支持的输入

这个 Skill 只处理公开、可访问的 `mp.weixin.qq.com` 公众号文章 URL，包括：

- `https://mp.weixin.qq.com/s/<token>`
- `https://mp.weixin.qq.com/s?__biz=...`

不处理视频号链接、私密/付费/朋友圈内容、需要登录态的账号数据、网页截图代替原文等情况。

## 两种正文形态

### 1. HTML 文本型文章

`read_wechat_article.py` 会从 `id="js_content"` 中提取文本，`manifest.json` 的
`image_only` 为 `false`，`extracted_text` 非空。可以直接用
`render_markdown.py` 生成可编辑 Markdown，再检查段落和图片是否完整。

### 2. 图片型文章

很多公众号正文是一张张海报或长图，`js_content` 里没有可复制的文字。此时：

- `image_only` 为 `true`；
- 所有图片按顺序下载到 `images/`；
- 使用 `ocr_images.py` 调用 macOS Vision 做中文 OCR；
- 代理必须逐张查看图片，识别章节标题、活动信息、二维码和授权要求；
- 不要仅凭 OCR 文本直接发布，OCR 需经人工核对。

## 识别与整理规则

1. 保留原文标题、账号、发布时间和所有数字、日期、人名、专有名词。
2. 原文出现“四大赛道”和“五条赛道”等前后不一致时，不要擅自统一；在
   `原文备注` 中记录差异。
3. 二维码、Logo、表格布局无法用文字完整还原时，保留原图并说明扫码位置。
4. 图片型文章要有清晰的章节结构，并保留 `images/` 相对路径，确保 Markdown
   可以离线阅读。
5. 如果文章含有版权标识或转载说明，整理稿应保留来源和归属。

## 常见失败

- 页面要求登录、验证或地域限制：停止并报告，不尝试绕过访问控制。
- 抓到的是错误页或验证页：检查标题、`js_content`、图片数量后重试。
- OCR 引擎缺失：在 macOS 上安装 Xcode Command Line Tools，或使用包含
  `chi_sim` 的 Tesseract；两者都没有时，代理使用视觉工具逐图整理。
- 图片下载失败：检查网络；部分图片可能带防盗链，重试或按 `manifest.json`
  中的原始 URL 处理。

## 输出结构

```text
<output-dir>/
├── article.html       # 原始 HTML（用于诊断和重跑）
├── manifest.json      # 元数据、正文文本、图片清单
├── images/            # 按顺序编号的原文图片
└── <slug>.md          # 可编辑 Markdown
```
