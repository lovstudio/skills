---
name: lov-quality-gate
description: >
  对完整公众号文章包执行结构、事实边界、文风、品牌、双比例图片、散列和可发布状态检查，输出机器可读报告。Use when the user asks to“验收文章包”“audit this WeChat article”或“检查封面和 manifest”。
license: MIT
compatibility: "Embedded module of lov-article-creator; Python 3.9+ and Pillow 10+."
depends_on:
  - lov-branding-consistency
metadata:
  author: LovStudio
  version: "0.3.1"
  tags: [quality-gate, wechat, validation]
  dependencies: []
---

# Quality Gate

确认文章包不仅“生成了”，而且在内容、模板、品牌、图片和状态上真的能交付。自动校验处理确定性规则，人工审阅处理事实与品味。

## Triggers

### Activate when

- “验收这套公众号文章和封面。”
- “只检查，不要改文章。”
- “Review this WeChat article package before publishing.”

### Do not activate when

- 输入仍是主题或资料，尚未形成文章包；先执行 `full` 管线。
- 用户明确要求发布；本模块只能验收，不能代替外部发布授权。
- 只检查一个普通 Markdown 文件且没有公众号结构要求；使用普通文档审查能力。

## Workflow

1. 读取 Kit 根目录 `references/quality-gate.md` 与 `references/output-contract.md`。
2. 运行 `scripts/validate_article_package.py --package PACKAGE --json`。
3. 人工核对关键数字、引语、链接、第一人称、标题承诺与正文证据。
4. 只保留标题与开头 300 字做 cold-reader test；若必须依赖聊天或旧稿才能理解，直接
   判为内容失败，不得用其他指标抵消。
5. 若文章包含调研、评测、benchmark、排名、总分或雷达图，逐项核对测试方法、完整 Prompt、指标定义、评分方法、评分示例、复现方法、原始产物索引和局限性，并确认它们在测试结果之前建立。
6. 人工回读分享封面和 `4:3` 正文首图：焦点、Logo、裁切、文字污染、缩略图与手机首屏。
7. `audit` 管线只报告；`full`、`rewrite`、`visual` 管线发现问题后修复并重跑。
8. 只有机器规则与人工语义检查都通过，才把结果标记为 `prepared`。

## Machine checks

- 必需文件与 JSON schema 可读。
- `article.md` 唯一 H1，`4:3` 正文首图位于开头区域。
- 标题、摘要、状态和相对路径满足输出契约。
- 分享封面与正文首图的尺寸、比例、文件散列与 manifest 一致。
- 研究评测类文章具备固定的方法章节，方法、Prompt、评分和复现均在结果之前；Prompt 区至少公开一份实际执行文本。
- 包内不泄露 `/Users/...`、`C:\\Users\\...` 等私有绝对路径。

## Human checks

- 关键结论有材料支持，推断被明确标出。
- 文风像真实作者，而不是统一腔调的 AI 说明书。
- 标题、摘要、开头与结论承诺一致。
- 目标读者无需知道旧稿、用户反馈或 Agent 工作过程，开头的所有指代都有可见先行词。
- 母品牌与发布主体分开，Logo 为发布主体官方白色横向 lockup，产品和延伸链接不冒充品牌。
- 分享封面适合消息列表，`4:3` 正文首图适合文章第一屏，二者角色独立且视觉语言一致。

## Dependencies

Python 3.9+ and Pillow 10+. The module validates artifacts and does not publish them.
