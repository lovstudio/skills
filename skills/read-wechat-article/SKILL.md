---
name: lov-read-wechat-article
description: >
  抓取公开公众号文章并转为可离线 Markdown；支持文字正文与图片海报、中文 OCR、保留原图与来源。Converts a public WeChat article URL into local Markdown.
license: MIT
compatibility: "Python 3.8+; macOS Vision or Tesseract; network access for public WeChat pages."
metadata:
  author: contributors
  version: "0.1.0"
  card_standard: lovstudio/skill-card/v1
  content_class: verbatim
  dependencies:
    - lov-branding-consistency
  tags:
    - wechat-official-account
    - markdown-export
    - article-archiving
    - ocr
---

# 公众号文章读取器 · WeChat Article Reader

把一条公开的微信公众号文章 URL 整理成本地可阅读、可编辑、可离线保存的
Markdown。文章本身有文字时直接提取；正文是海报、长图或设计图时，下载原图、
做中文 OCR，再由代理逐图核对和分章整理。整理稿保留原文标题、账号、时间、
数字、专有名词、二维码位置和原图，不擅自改写原文表述。

## Triggers

### Activate when

- 用户说“把这个公众号文章整理成 Markdown”“读取这篇微信文章并导出本地 md”。
- 用户给出 `mp.weixin.qq.com` 文章链接，要求保存正文、图片、来源或离线稿。
- User asks “Convert this WeChat article to Markdown”, “Read this public WeChat Official Account article”, or “Save this article locally”.

### Do not activate when

- 用户要发布、编辑或同步远端公众号草稿；交给 `lov-publish-wechat-article`。
- 用户要下载公众号视频号、抖音、小红书等媒体；交给 `lov-media-crawler`。
- 用户要绕过登录、付费、私密、地域限制或访问控制；本 Skill 不做任何绕过。
- 用户只是要分析本地已有 Markdown，不涉及公众号 URL；交给文章审计或创作能力。

## User Profile (cross-session)

每次运行读取 `skill.yaml` 声明的 `user-profile/v1`：用户语言、工作区、共享偏好，
以及 `skills.lov-read-wechat-article` 下的 Skill 记录。解析顺序为当前请求、项目
上下文、Skill 记录、共享偏好、用户 Profile、安全默认值。

用户明确说出的持久偏好，例如默认输出目录或 OCR 偏好，通过以下命令写入 Profile：

```bash
python3 "$SKILL_DIR/scripts/profile_store.py" record \
  --skill-id lov-read-wechat-article \
  --path records.output_dir \
  --value '"/path/to/output"' \
  --confirm
```

不要把 Cookie、Token、登录态或推断出的私人信息写入 Profile。

## Skill Group Composition

运行前阅读 [`references/skill-composition.md`](references/skill-composition.md)。
本 Skill 独立拥有“公开公众号 URL → 本地 Markdown + 原图”的验收。相邻能力只通过
URL、本地 Markdown 或本地媒体交接，不是隐藏依赖。

## Workflow (MANDATORY)

**必须按以下顺序执行。**

### Step 0: 解析根目录、Profile 与运行时

使用 `SKILL_DIR`；未提供时从当前 Skill 上下文推断。确认以下资源存在：

- `scripts/read_wechat_article.py`
- `scripts/ocr_images.py`
- `scripts/vision_ocr.swift`
- `scripts/render_markdown.py`
- `scripts/profile_store.py`
- `references/user-profile.md`
- `references/skill-composition.md`
- `references/wechat-extraction.md`

手工运行时：

```bash
export SKILL_DIR="/path/to/lov-read-wechat-article"
python3 "$SKILL_DIR/scripts/profile_store.py" read \
  --skill-id lov-read-wechat-article --pretty
```

### Step 1: 确定 URL、输出目录与权限

只处理用户有权访问和保存的公开内容。优先使用：

1. 用户当前请求中指定的输出目录；
2. `records.output_dir` 中的持久默认值；
3. 当前项目输出目录或 `./wechat-articles/<slug>`。

如果目录已存在同名 Markdown，不得覆盖；追加时间戳或序号生成新目录。

### Step 2: 抓取与提取

```bash
python3 "$SKILL_DIR/scripts/read_wechat_article.py" URL \
  --output-dir OUTPUT_DIR
```

脚本会生成 `manifest.json`、`article.html` 和 `images/`。阅读 `manifest.json`：

- `image_only=false`：直接跳到 Step 4；
- `image_only=true`：进入 Step 3；
- 图片数量为 0、标题为空或正文为空：先检查是否抓到验证页，再决定是否重试或停止。

详细字段与失败处理见
[`references/wechat-extraction.md`](references/wechat-extraction.md)。

### Step 3: 图片型文章的 OCR 与视觉核对

先检查 OCR 运行时：

```bash
python3 "$SKILL_DIR/scripts/ocr_images.py" --doctor
```

再执行 OCR：

```bash
python3 "$SKILL_DIR/scripts/ocr_images.py" \
  --image-dir OUTPUT_DIR/images \
  --output OUTPUT_DIR/ocr.json
```

OCR 完成后，必须逐张使用视觉工具查看 `images/` 中的原图，核对：

- 章节标题、活动时间、地点、奖池、报名信息；
- 数字、日期、人名、公司名和 Logo；
- 二维码、表格、海报中的小字；
- 原文前后不一致时，不要静默修正，记入 `原文备注`。

### Step 4: 生成 Markdown 草稿

```bash
python3 "$SKILL_DIR/scripts/render_markdown.py" \
  OUTPUT_DIR/manifest.json \
  --ocr OUTPUT_DIR/ocr.json \
  --output OUTPUT_DIR/<slug>.md
```

该命令生成结构化草稿。随后由代理完成：

- 文字型文章：合并断行、保留段落，检查来源和图片引用；
- 图片型文章：把 OCR 草稿整理成与海报一致的章节，删除机器噪声；
- 保留所有原文数字、专有名词和原图；
- 二维码无法还原时，保留原图并注明扫码位置。

### Step 5: 加来源与原文备注

Markdown 末尾必须有：

- 原始 URL、公众号、发布时间；
- 原图目录说明；
- 任何发现的事实差异、OCR 不确定项、无法通过文本还原的内容；
- 若原文有版权或转载标识，保留归属说明。

### Step 6: 验证交付

确认：

1. `manifest.json`、`<slug>.md` 存在且非空；
2. Markdown 中所有 `images/` 引用都能在本地解析；
3. 图片型文章至少包含原图，且正文文字没有凭空补充；
4. 没有把 Cookie、Token、登录态或私人路径写入交付物；
5. 输出目录可以被用户直接打开、编辑或分享。

完成后报告 Markdown 路径、原图数量、OCR 引擎和任何原文差异备注。

## Dependencies

- Python 3.8+
- PyYAML（运行 `scripts/validate_skill.py` 时需要）
- 网络访问：读取公开 `mp.weixin.qq.com` 页面
- macOS Vision：用于中文图片 OCR（推荐，需 Xcode Command Line Tools）
- 可选 Tesseract：需要 `chi_sim` 语言包时的回退方案
- `lov-branding-consistency`：整理稿面向读者，保留来源及原文事实边界
