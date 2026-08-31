# 输出契约

完整文章包位于 `output/articles/<slug>/`。`slug` 使用 ASCII lowercase kebab-case。

## 必需文件

```text
article.md
article-manifest.json
sources.md
cover/art-master.png
cover/wechat-cover-wide.png
cover/wechat-cover-wide.jpg
cover/article-opening-4x3.png
cover/article-opening-4x3.jpg
cover/cover-manifest.json
quality-report.json
```

品牌化完整版本还必须在结论与品牌尾注之间包含且仅包含一种封面说明：真实作品使用“本期封面”，生成式底图使用“封面 Prompt”。来源、权利或实际 Prompt 必须能回到本次封面制作记录。

`repost` 管线另外输出：

```text
source-page.html
source-content.html
source-text.txt
source-meta.json
source-assets/
edition-manifest.json
repost-audit.json
```

其中 `edition-manifest.json` 至少记录来源 URL、来源账号、冻结正文散列、来源图片数、`copyrightMode: reprint` 与新增区块。远端 HTML 和 publication receipt 不属于本地创建完成条件。

`article.md` 引用的本地正文图片必须按原相对路径复制进文章包，例如 `figures/radar.png`。构建器拒绝不存在、包含 `..` 或使用本机绝对路径的图片；远程图片保留给下游获取与上传流程处理。

## article-manifest.json

必需字段：

- `schema`: `lovstudio/wechat-article-package/v2`
- `title`, `slug`, `excerpt`, `author`, `language`
- `article_path`
- `opening_image_path`
- `wide_cover_path`
- `read_original_url`
- `source_items`
- `body_image_paths`：已复制进包内的本地正文图片相对路径
- `brand.name`, `brand.logo_source`, `brand.site`
- `created_at`

本地 Profile 路径、密钥、Cookie、未公开账号标识和内部工作备注不得进入 manifest。

`article-manifest.json` 必须分开记录 `brand` 与 `publication`。`cover-manifest.json` 必须将 `publication.logo_variant` 记录为 `horizontal-lockup`、`publication.logo_color` 记录为 `white`，并记录宽高比与白色像素比例；私有 Logo 文件路径只以 Profile 引用表示。

## sources.md

每项来源记录标题、URL 或公开仓库路径、版本或检查日期、在文章中支持的结论。私人研究路径只用于当前任务，不写入公开 sources。

## 状态

- `pending_validation`：文章与视觉文件已生成，尚未通过本地质量门；这是内部过渡状态。
- `prepared`：本地文章包完整并通过质量门。
- `draft_created`：下游发布 Skill 已在公众号远端草稿箱回读到 `media_id`。
- `published`：下游发布 Skill 已查询到公开文章标识或 URL。

本 Skill 默认只报告 `prepared`，不能把本地生成写成已进入草稿箱或已发布。
