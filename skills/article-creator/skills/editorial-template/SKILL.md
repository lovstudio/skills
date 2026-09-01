---
name: lov-editorial-template
description: >
  把正文装配成统一的微信公众号文章结构，补齐标题、摘要、4:3 正文首图位置、来源、延伸阅读、品牌尾注与 manifest。Use when the user asks to“套公众号模板”“package this draft”或“add editorial metadata”。
license: MIT
compatibility: "Embedded module of lov-article-creator; Python 3.9+ for deterministic packaging."
depends_on:
  - lov-branding-consistency
metadata:
  author: LovStudio
  version: "0.4.0"
  tags: [wechat, editorial-template, packaging]
  dependencies: []
---

# Editorial Template

把写好的内容变成结构稳定、可继续进入视觉与发布环节的公众号文章包。固定的是语义位置和交付字段，不是每篇文章都长得一样。

## Triggers

### Activate when

- “给这篇文章套上统一的公众号模板。”
- “补齐摘要、来源、延伸阅读和品牌尾注。”
- “Package this draft as a WeChat article with metadata.”

### Do not activate when

- 输入仍是一堆未整理材料；先交给 `lov-article-writing`。
- 只需要生成图片；交给 `lov-cover-package`。
- 要把文章写进微信后台；交给下游 Operator 或 Publisher。

## Template contract

文章按实际内容使用以下语义顺序：

1. canonical 源文件中的唯一一级标题；发布到微信时仅写入平台标题字段，正文默认隐藏；
2. `cover/article-opening-4x3.jpg` 横向正文首图；
3. 导语；
4. 正文与稳定的 H2/H3；canonical Markdown 默认不写死呈现型 TOC，Lovpen 微信 HTML
   根据最终章节生成目录；
5. 结论或“写在最后”；
6. 真实存在的代码、原文、博客或延伸阅读；
7. 稳定品牌尾注。

没有真实链接时删掉对应组件，不写“敬请期待”占位。`publication`、`brand` 和 `products` 必须在 manifest 中分开，不能把品牌官网冒充原文地址。

## Workflow

1. 读取 Kit 根目录 `references/article-template.md` 与 `references/output-contract.md`。
2. 确认标题、摘要、作者、slug、发布主体、来源和 `read_original_url`。
3. 在一级标题之后、导语之前插入独立的 `4:3` 正文首图；已有正确引用时不得重复插入。
4. 保留正文原有论证层级，只修复模板位置、重复标题和缺失元数据。
5. 将正文中穿插的来源、参考资料和引申链接统一降级为小字斜体资料注；多项资料逐项
   分行或分点，不挤成一段，也不集中堆到文末。主要行动入口单独保留，不与资料链接
   混排。
6. 运行 Kit 根目录 `scripts/build_article_package.py` 建立 `article.md`、manifest 与 `sources.md`，并把正文引用的本地图片按原相对路径复制进包内。
7. 检查输出中没有用户私有绝对路径、临时文件地址或未解析占位符。

## Acceptance

- `article.md` 只有一个 H1，首图位于 H1 与第一个 H2 之间。
- manifest 能区分文章、品牌、产品、来源与发布状态。
- `read_original_url` 只在真实线上版本存在时填写。
- 默认状态是 `prepared`；本地生成不冒充“已进草稿箱”或“已发布”。
- 包内路径均为可迁移的相对路径。

## Dependencies

Python 3.9+ for the Kit packaging script. No sibling Skill dependency.
