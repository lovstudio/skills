---
name: lovstudio:tech-book
category: Content Creation
tagline: "O'Reilly 风格技术书逐章写作，压缩摘要策略突破上下文窗口限制"
description: >
  Write O'Reilly-style technical books chapter by chapter using a GitHub repo
  as the single source of truth. Solves LLM context window limitations through
  a compressed book summary strategy (OUTLINE + BOOK_SUMMARY ≈ 9KB overhead).
  5-phase workflow: Plan → Research → Write → Review → Build. Outputs mdBook
  HTML (GitHub Pages) and pandoc PDF (CJK-ready). Trigger when user mentions
  "写书", "技术书", "tech book", "O'Reilly", "写一本书", "book writing",
  "mdbook", "逐章写作", or wants to create a multi-chapter technical book.
license: Commercial
compatibility: >
  Requires mdbook (cargo install mdbook or brew install mdbook),
  pandoc + basictex (brew install pandoc basictex),
  gh CLI (brew install gh). Optional: context7 MCP for live docs.
metadata:
  author: lovstudio
  version: "0.2.0"
  tags: book writing cjk mdbook pandoc
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
│   └── references.md      # 全书参考文献
├── references/            # 预置参考文献库
├── assets/images/         # 图片、图表
├── scripts/               # 构建脚本
└── .github/workflows/     # GitHub Actions 自动构建
```

## Workflow

Read [references/workflow.md](references/workflow.md) for the complete 5-phase workflow.

**Phase summary:**

1. **Plan** — Collect book info → OUTLINE.md → repo skeleton → initial commit
2. **Research** — WebSearch + context7 → refs.md per chapter
3. **Write** — One chapter per session, load OUTLINE + BOOK_SUMMARY + refs + glossary
4. **Review** — Consistency, terms, cross-references, polish
5. **Build** — mdBook → HTML | Pandoc → PDF (CJK-ready)

## Context Window Strategy (MANDATORY)

每次写作新章节时，MUST 加载以下文件：

1. `OUTLINE.md` — 全局大纲（理解全书结构）
2. `BOOK_SUMMARY.md` — 全书压缩摘要（理解已写内容）
3. `src/chapter-xx/refs.md` — 当前章参考文献（如有）
4. `glossary.md` — 术语表（保持术语一致）

**不要加载其他章节全文** — 这是上下文窗口管理的关键。

## Writing Style

- 语言：中文正文，代码/术语保留英文原文
- 风格：O'Reilly 实战派 — 概念解释 → 代码示例 → 最佳实践 → 常见陷阱
- 每章开头用一个实际问题或场景引入
- 每章末尾加 "本章小结" + "延伸阅读"
- 完成后更新 BOOK_SUMMARY.md（≤500 字）+ glossary.md

## Dependencies

```bash
cargo install mdbook    # or: brew install mdbook
brew install pandoc basictex
brew install gh
```
