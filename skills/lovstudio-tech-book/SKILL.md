---
name: lovstudio:tech-book
category: Content Creation
tagline: "Write O'Reilly-style technical books chapter by chapter, with a GitHub repo as the single source of truth."
description: >
  Write professional technical books (O'Reilly style) with full chapter management,
  reference sourcing, and multi-format output (mdBook HTML + Pandoc PDF).
  Solves the LLM context window limitation by maintaining a compressed book summary
  + current chapter strategy. All content lives in a GitHub repo.
  Use when the user says "写书", "write a book", "写技术书", "tech book",
  "出一本书", "book project", "O'Reilly", "写一本关于…的书",
  "create a book about", "start a book", "book repo".
license: MIT
compatibility: >
  Requires: mdBook (`cargo install mdbook` or `brew install mdbook`),
  pandoc + basictex (`brew install pandoc basictex`) for PDF,
  gh CLI for repo management. Cross-platform with caveats on PDF (macOS recommended).
metadata:
  author: lovstudio
  version: "0.1.0"
  tags: book writing technical authoring oreilly mdbook pandoc
---

# tech-book — O'Reilly 风格技术书写作

以 GitHub repo 为单一数据源，逐章写作专业技术书籍。通过「全书压缩摘要 + 当前章全文」策略解决上下文窗口限制。

## When to Use

- 用户想写一本完整的技术书籍（非单篇文章）
- 用户提到 O'Reilly、技术书、写书、出书
- 用户想把系列技术内容组织成书

## Repo Structure

每本书是一个独立 GitHub repo，结构如下：

```
book-repo/
├── book.toml              # mdBook config
├── SUMMARY.md             # mdBook TOC (auto-generated from OUTLINE.md)
├── OUTLINE.md             # 全局大纲 — 每次写作会话必须加载
├── BOOK_SUMMARY.md        # 全书压缩摘要 — 每章≤500字，每次写作加载
├── bibliography.md        # 完整参考文献（BibTeX 风格）
├── glossary.md            # 术语表（中英对照）
├── src/                   # mdBook source
│   ├── SUMMARY.md         # mdBook 目录（从 OUTLINE.md 生成）
│   ├── chapter-01/
│   │   ├── README.md      # 章节正文
│   │   ├── section-01.md  # 小节（大章节拆分时用）
│   │   └── refs.md        # 本章参考文献 + 研究笔记
│   ├── chapter-02/
│   │   └── ...
│   ├── appendix-a.md
│   └── references.md      # 全书参考文献（链接到 bibliography.md）
├── references/            # 预置参考文献库
│   ├── core-papers.md     # 核心论文列表
│   ├── official-docs.md   # 官方文档链接
│   └── datasets.md        # 数据集/benchmark 引用
├── assets/                # 图片、图表
│   └── images/
├── scripts/
│   ├── build-html.sh      # mdbook build
│   ├── build-pdf.sh       # pandoc 全书 PDF
│   └── sync-summary.sh    # OUTLINE.md → src/SUMMARY.md
└── .github/
    └── workflows/
        └── build.yml      # GitHub Actions: push 时自动构建
```

## Workflow (MANDATORY)

**You MUST follow these steps in order. Each major phase is a separate conversation session.**

---

### Phase 1: Book Planning (首次调用)

Use `AskUserQuestion` 收集以下信息：

1. **书名 + 副标题**
2. **目标读者**（初学者 / 中级 / 高级 / 混合）
3. **核心主题**（用户描述想写什么）
4. **预期章节数**（推荐 8-15 章）
5. **特殊要求**（是否需要代码示例 repo、是否需要习题等）

然后执行：

1. 用 `gh repo create` 创建 GitHub repo（private by default）
2. 生成 `OUTLINE.md`：
   - 每章标题 + 3-5 行内容摘要
   - 标注章节间依赖关系
   - 标注每章预估字数（中文 5000-8000 字/章为宜）
3. 生成 `book.toml`（mdBook 配置）
4. 生成空的目录结构（所有 chapter-xx/ 文件夹 + 空 README.md）
5. 生成 `references/core-papers.md`：用 WebSearch 搜索该领域核心论文/文档，整理初始参考文献库
6. 生成 `BOOK_SUMMARY.md`（初始为每章一行 placeholder）
7. 生成构建脚本（`scripts/build-html.sh`, `scripts/build-pdf.sh`, `scripts/sync-summary.sh`）
8. 初始 commit + push

**交付物**：一个可 clone 的 repo，包含完整大纲和空章节骨架。

---

### Phase 2: Research & References (可选，推荐)

针对每章补充参考文献：

1. 读取 `OUTLINE.md` 确定当前章主题
2. 用 `WebSearch` 搜索：
   - arxiv 最新论文（关键词 + "2024" or "2025" or "2026"）
   - 官方文档 / API reference
   - 高质量博客文章 / 技术演讲
3. 用 `context7` MCP 拉取框架/库的官方文档片段
4. 将搜索结果整理到 `src/chapter-xx/refs.md`：
   ```markdown
   ## 参考文献

   1. [论文标题](url) — 作者, 年份. 一句话摘要.
   2. [文档标题](url) — 访问日期: YYYY-MM-DD. 相关内容概述.
   ```
5. 更新 `bibliography.md`
6. Commit + push

---

### Phase 3: Chapter Writing (核心循环 — 每章一次会话)

**上下文加载策略（MANDATORY）：**

每次写作新章节时，MUST 加载以下文件：

1. `OUTLINE.md` — 全局大纲（理解全书结构）
2. `BOOK_SUMMARY.md` — 全书压缩摘要（理解已写内容）
3. `src/chapter-xx/refs.md` — 当前章参考文献（如有）
4. `glossary.md` — 术语表（保持术语一致）

**不要加载其他章节全文** — 这是上下文窗口管理的关键。

写作流程：

1. **加载上下文**：读取上述 4 个文件
2. **生成章节大纲**：基于 OUTLINE.md 中该章的描述，展开为小节级大纲，用 `AskUserQuestion` 确认
3. **逐节写作**：
   - 每小节 1000-2000 字
   - 代码示例必须可运行（标注语言和依赖）
   - 引用标注格式：`[^1]`，对应 refs.md 中的条目
   - 术语首次出现时中英对照：`注意力机制（Attention Mechanism）`
4. **章末总结**：每章末尾加 "本章小结" + "延伸阅读"
5. **更新 BOOK_SUMMARY.md**：为刚完成的章节写 ≤500 字压缩摘要
6. **更新 glossary.md**：添加本章新术语
7. Commit + push

**写作风格指南：**

- 语言：中文正文，代码/术语保留英文原文
- 风格：O'Reilly 实战派 — 概念解释 → 代码示例 → 最佳实践 → 常见陷阱
- 每章开头用一个实际问题或场景引入
- 避免纯理论堆砌，每个概念必须有代码或图示
- 段落简短，多用列表和代码块
- 中文排版：中英文之间加空格，数字与中文之间加空格

---

### Phase 4: Review & Polish (每几章做一次)

1. 加载 `BOOK_SUMMARY.md` 检查全书一致性
2. 检查术语一致性（`glossary.md` vs 正文用法）
3. 检查引用完整性（所有 `[^n]` 都有对应 refs.md 条目）
4. 检查章节间衔接（前一章结尾 → 后一章开头）
5. 输出修订建议，用户确认后批量修改
6. Commit + push

---

### Phase 5: Build & Publish

```bash
# 构建 HTML 书籍（mdBook）
bash scripts/build-html.sh

# 构建 PDF（Pandoc）
bash scripts/build-pdf.sh

# 部署到 GitHub Pages
# (GitHub Actions 自动处理，push 即可)
```

## Build Scripts Reference

### scripts/build-html.sh

```bash
#!/bin/bash
mdbook build
echo "HTML output: book/"
```

### scripts/build-pdf.sh

```bash
#!/bin/bash
# Concatenate all chapters in order
cd src
cat $(grep '.md' SUMMARY.md | sed 's/.*(\(.*\))/\1/' | tr '\n' ' ') > /tmp/full-book.md
cd ..
pandoc /tmp/full-book.md \
  -o output/book.pdf \
  --pdf-engine=xelatex \
  -V mainfont="PingFang SC" \
  -V monofont="Menlo" \
  -V geometry:margin=2.5cm \
  --toc --toc-depth=2 \
  --highlight-style=tango
echo "PDF output: output/book.pdf"
```

### scripts/sync-summary.sh

```bash
#!/bin/bash
# Generate src/SUMMARY.md from OUTLINE.md
# This is a helper — you may also edit SUMMARY.md directly
echo "# Summary" > src/SUMMARY.md
echo "" >> src/SUMMARY.md
# Parse OUTLINE.md and generate mdBook-compatible links
grep -E "^#{1,2} " OUTLINE.md | while read -r line; do
  level=$(echo "$line" | grep -o "^#*" | wc -c)
  title=$(echo "$line" | sed 's/^#* //')
  slug=$(echo "$title" | tr '[:upper:]' '[:lower:]' | tr ' ' '-' | tr -cd 'a-z0-9-')
  if [ "$level" -eq 2 ]; then
    echo "- [$title](chapter-${slug}/README.md)" >> src/SUMMARY.md
  elif [ "$level" -eq 3 ]; then
    echo "  - [$title](chapter-${slug}/README.md)" >> src/SUMMARY.md
  fi
done
echo "Generated src/SUMMARY.md"
```

## BOOK_SUMMARY.md Format

这是上下文窗口管理的核心文件。每章完成后必须更新。

```markdown
# Book Summary (Auto-maintained — DO NOT edit manually except after chapter completion)

## Chapter 1: [标题]
Status: ✅ Done | 📝 Draft | ⬜ Not started
Word count: ~5000
Key points:
- 核心观点1（一句话）
- 核心观点2（一句话）
- 核心观点3（一句话）
Cross-references: Links to Chapter 3, 5
New terms: 术语A, 术语B

## Chapter 2: [标题]
Status: ⬜ Not started
...
```

## Data Source Strategy

### 预置参考文献库 (`references/`)

在 Phase 1 创建时初始化，包含：

- `core-papers.md` — 该领域经典论文（用 WebSearch 搜索整理）
- `official-docs.md` — 框架/工具官方文档链接
- `datasets.md` — 常用数据集和 benchmark

### 实时搜索补充

写作每章时，用以下工具补充最新内容：

- `WebSearch` — 搜索 arxiv, blog posts, release notes
- `context7` MCP — 拉取框架/库的最新官方文档
- `WebFetch` — 抓取特定页面内容

所有引用必须标注：
```markdown
[^1]: Author, "Title", URL, 访问日期: YYYY-MM-DD
```

## Dependencies

```bash
# mdBook (HTML 构建)
cargo install mdbook
# 或
brew install mdbook

# Pandoc + LaTeX (PDF 构建)
brew install pandoc basictex

# GitHub CLI (repo 管理)
brew install gh
```

## Tips

- **一次会话只写一章** — 这是设计核心，不要试图在一次会话里写多章
- **BOOK_SUMMARY.md 是续写的桥梁** — 每章完成后立即更新，下次会话依赖它
- **refs.md 先行** — 先整理参考文献，再写正文，质量更高
- **图片用 Mermaid** — 在 Markdown 中用 mermaid 语法画图，mdBook 原生支持
- **代码示例独立可运行** — 读者应该能直接复制运行
