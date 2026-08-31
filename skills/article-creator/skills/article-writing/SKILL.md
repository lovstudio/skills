---
name: lov-article-writing
description: >
  把研究材料、采访、笔记或旧稿整理成有事实边界、有核心判断、适合移动阅读的公众号正文。Use when the user says“先把文章写出来”“按我的文风重写”或“write the WeChat article body”。
license: MIT
compatibility: "Embedded module of lov-article-creator; portable Markdown workflow."
depends_on:
  - lov-branding-consistency
  - lov-writing-style
metadata:
  author: LovStudio
  version: "0.4.0"
  tags: [wechat, article-writing, fact-led]
  dependencies: []
---

# Article Writing

把输入材料整理成公众号正文写作任务，并交给 `lov-writing-style` 完成文风适配；后者内置调用 `lov-human-writing` 做作者性审计。这个模块只拥有公众号题材与结构约束，不再维护第二套通用写作或“去 AI 味”规则。

## Triggers

### Activate when

- “根据这些资料先把公众号正文写出来。”
- “保留事实，按我的文风重写这篇文章。”
- “Write or rewrite the article body from these sources.”

### Do not activate when

- 只需要封面或首图；交给 `lov-cover-package`。
- 只需要检查现有成品；交给 `lov-quality-gate`。
- 用户要求直接发布到公众号；交给独立发布能力。

## Inputs and outputs

输入可以是主题、笔记、网页摘录、研究文件、访谈记录或旧稿。输出是一份事实受约束的 Markdown 正文草稿，供 `lov-editorial-template` 接收。

内部先建立 truth ledger，至少区分：确定事实、来源主张、真实第一人称经历、作者判断、内部上下文、证据缺口。truth ledger 不默认进入公开文章。另建 reader contract，明确读者打开文章时只知道标题、成品前文和公共事实，不知道聊天、旧稿与审稿意见。

## Workflow

1. 完整读取输入，不从摘要或文件名猜正文。
2. 用一句话写出文章要推动的核心判断；如果只能复述材料，命题还没有成立。
3. 标注每个关键数字、引语、版本和因果判断的来源或边界。
4. 选择最有张力的真实入口，让核心冲突或判断在前 300 字出现。
5. 对标题与开头 300 字做 cold-reader test：移除聊天与旧稿后仍能独立理解；悬空的
   “前一版 / 这次重写 / 按你的要求”直接失败。
6. 按定义、区分、证据、代价、行动组织正文；章节服务于论证，不套万能小标题。
7. 识别研究评测类文章。只要正文包含排名、总分、雷达图或方法优劣，就按“调研对象 → 测试方法 → Prompt → 评价指标 → 评分方法 → 评分示例 → 复现方法 → 测试结果 → 局限性 → 结论”组织；方法与评分规则必须先于结果。
8. 研究评测类章节使用朴素、可检索的论文式标题。`测试方法`、`Prompt`、`评价指标`、`评分方法` 等标题本身不承担网感，不改写成提问句、悬念句或“这 63 次到底怎么跑出来的”式标题。
9. 在 `Prompt` 中公开实际执行文本；在 `评价指标` 中定义每个维度测量什么、不测什么；在 `评分方法` 中公开量表、权重、盲评、随机化和聚合方式；在 `评分示例` 中从一份原始判断演算到一个公开分数；在 `复现方法` 中给出冻结版本、环境、命令、随机种子、原始产物和校验散列。
10. 把 truth ledger、reader contract、目标读者、文章题材、结构要求与正文草稿交给 `lov-writing-style`；由它读取用户文风 Profile，并调用 `lov-human-writing`。
11. 接收写作结果后只做公众号结构验收，不在本模块另行维护表层禁词清单或模拟“人味”。

Kit 根目录 `references/writing-style.md` 只保留公众号渠道补充，不是文风 canonical source。当前请求、真实材料和用户明确修改始终优先。

## Acceptance

- 开头 300 字内出现冲突、结果、现场或核心判断。
- 每个主要章节至少有一项事实、案例、数字、亲历或来源。
- 事实、作者判断和推测能够被读者区分。
- 第一人称只用于真实经历和真实立场。
- 正文能够独立成立，不依赖封面替它解释主题。
- 正文能够独立成立，不依赖当前会话、旧稿或审稿者替它补充前因。
- 研究评测类文章的方法、Prompt、指标、评分和复现信息足够让第三方理解分数来源；所有榜单与雷达图均能回到原始输入、输出和评分记录。

## Dependencies

`lov-writing-style`，并由其组合 `lov-human-writing`。本模块随 Kit 分发，只交接 Markdown 与写作账本。
