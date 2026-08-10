---
name: sgc-rich-export
description: 将一份面向用户的内容稳定导出为单文件 HTML、带 assets 的 HTML 文件夹、Markdown、DOCX 与 PDF，并按格式正确处理图片、音频、视频和嵌入式交互内容。用于“富媒体导出”“一键导出”“导出 html/pdf/docx/md”“离线网页”“交付包”“给产品接导出能力”等需求，以及需要为产品建立可复用内容导出管线时。
license: MIT
metadata:
  author: lovstudio
  version: 0.1.0
  tags:
    - export
    - html
    - pdf
    - docx
    - rich-media
---

# 富媒体一键导出

把内容先收敛为一个可审计的源，再针对每个交付格式生成其能忠实表达的版本。HTML 保留交互媒体；DOCX、PDF 和 Markdown 生成可编辑或可打印的静态投影，并为媒体保留封面、说明和原链接。

## Triggers

- 用户要求把一份内容或产品数据一键导出为 HTML、Markdown、DOCX、PDF、ZIP 或离线交付包。
- 用户要求导出含图片、音频、视频、iframe、交互图表或媒体说明的内容，并需要针对不同格式正确处理。
- 用户需要给 Web、桌面端或服务端产品接入可复用的多格式导出能力。

### Do not activate when

- 只需要编辑一个已有 DOCX、PDF 或网页中的局部内容，且不涉及多格式交付。
- 只需要生成单张图片、单个幻灯片或一个视频文件；使用对应的媒体制作工作流。

## 先做内容边界

1. 将聊天中的人名、项目背景、内部状态、提示词、创作过程视为内部上下文；只有用户要求出现在成品中的字段才进入输入内容。
2. 生成标题、作者、封面、页脚和文件名时，只读取显式 `document` 元数据；不要从聊天背景推断或补入个人信息。
3. 有视频、音频、地图、嵌入网页或交互图表时，先声明其静态投影。没有封面时，PDF/DOCX 至少保留名称、摘要和可访问链接。

## 输入与命令

默认输入为 `.md`；也支持 `.html` 和本 Skill 定义的 `rich-export.json`。输入中的相对资源相对输入文件解析。

```bash
python3 "$SKILL_DIR/scripts/export_rich.py" \
  --input ./release/article.md \
  --out ./release/exports \
  --formats html-single,html-dir,md,docx,pdf \
  --zip
```

先通过 `--formats` 只生成用户所需格式。`html-single` 适合直接发送和离线打开；`html-dir` 适合视频大、文件多或需要保留媒体原文件；`docx` 适合继续编辑；`pdf` 适合打印和归档；`md` 是可追溯源稿。

运行 `python3 "$SKILL_DIR/scripts/export_rich.py" --help` 查看依赖与选项。完整输入契约见 [references/format-contract.md](references/format-contract.md)，产品集成见 [references/product-integration.md](references/product-integration.md)。

## 渲染策略

| 目标 | 生成方式 | 媒体行为 |
|---|---|---|
| 单文件 HTML | Pandoc `--embed-resources` | 内嵌图片、样式、脚本、音视频；大文件会显著膨胀 |
| HTML 文件夹 | Pandoc + `assets/` | 保持交互与独立资源，适合实际分发 |
| Markdown | Pandoc 规范化 | 保留图片和链接；媒体使用显式链接 |
| DOCX | Pandoc + 可选 reference.docx | 图片嵌入；视频/音频/iframe 投影为封面、说明与链接 |
| PDF | Chromium/Playwright 打印静态 HTML | 图片和版式保留；媒体投影为封面、说明与链接 |

不要把单文件 HTML 当作大型视频的默认交付。媒体总量超过约 20 MB 时默认同时交付 `html-dir`；若用户必须只收一个文件，交付 ZIP，其中包含 HTML 文件夹和 `export-manifest.json`。

## 验收

每次导出后执行以下检查：

1. 打开单文件 HTML 并断网刷新；检查字体、图片、音视频控件、目录和链接。
2. 解压/打开 HTML 文件夹；检查 `index.html` 的所有资源均来自包内，且没有绝对本机路径。
3. 用 Word/LibreOffice 打开 DOCX；检查中文字体、表格、图片、分页及每个媒体链接。
4. 渲染 PDF 首页、含图片页、含媒体投影页和末页；检查裁切、溢出、乱码、链接和页码。
5. 检查 `export-manifest.json` 的 `warnings`；不得把内部元数据或提示词当作正文导出。

## 选择与限制

- 默认采用 Pandoc + Playwright：前者负责结构化格式互转，后者将已经确认的网页版式稳定打印为 PDF。
- 现有 `sgc-any2pdf`、`sgc-any2docx` 仍适合中文长文的专门美术排版；本 Skill 负责多格式同源交付和富媒体降级策略。
- 不将 SingleFile CLI 作为产品内置依赖：其开源仓库为 AGPL，且它更适合网页存档，不是多格式内容发布管线。
- HTML 与打印/办公格式并非等价。交互图表、iframe 和媒体播放能力只在 HTML 保真；其他格式应把信息和访问路径交付完整，而不是伪装成可播放内容。
