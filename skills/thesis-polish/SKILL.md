---
name: lovstudio:thesis-polish
category: Content Processing
tagline: "MBA 论文全面润色，对标全国优秀论文标准。语言+结构+论证+创新四维提升。"
description: >
  Polish and elevate MBA thesis / dissertation to national outstanding thesis
  quality (全国优秀论文). Performs comprehensive improvement: academic language,
  argument structure, logical rigor, innovation highlights, and formatting.
  Input: markdown thesis text. Output: polished full text.
  Also trigger when the user mentions "论文润色", "MBA论文", "优秀论文",
  "thesis polish", "dissertation improvement", "学术润色".
license: MIT
compatibility: >
  Pure instructions — no dependencies. Works with any Claude model.
metadata:
  author: lovstudio
  version: "1.0.0"
  tags: thesis academic writing MBA polish 论文 润色
---

# thesis-polish — MBA 论文全面润色

将 MBA 论文从初稿提升至全国优秀论文水准。涵盖语言润色、结构优化、论证强化、创新点凸显四个维度。

## When to Use

- 用户提供 MBA 论文（markdown 格式）需要润色
- 用户想让论文达到全国优秀论文标准
- 用户需要学术写作的全面提升

## Workflow (MANDATORY)

### Step 1: 接收论文

读取用户提供的论文文件（markdown 格式）。如果用户给的是文件路径，用 Read 工具读取。

### Step 2: 诊断评估

通读全文后，先输出一份**诊断报告**（不超过 300 字），包含：

| 维度 | 当前水平 | 主要问题 | 提升方向 |
|------|---------|---------|---------|
| 语言表达 | A/B/C | ... | ... |
| 论证逻辑 | A/B/C | ... | ... |
| 结构布局 | A/B/C | ... | ... |
| 创新贡献 | A/B/C | ... | ... |
| 文献运用 | A/B/C | ... | ... |

### Step 3: 确认润色策略

**Use `AskUserQuestion` to confirm strategy BEFORE polishing.**

向用户展示诊断报告后，询问：

- 是否同意诊断？有无特殊要求？
- 论文的核心创新点是什么？（帮助 AI 更好地凸显）
- 是否有目标期刊/评审标准的特殊要求？

### Step 4: 逐章润色

按章节逐一润色，每章输出完整的润色后文本。润色时严格遵循以下标准：

#### 4.1 语言表达标准

- **学术用语**：口语化表达 → 学术规范用语（"很多" → "大量/众多"，"觉得" → "认为/表明"）
- **句式升级**：简单句 → 复合句，增加因果、转折、递进的逻辑连接
- **术语一致**：全文术语统一，首次出现标注英文原文
- **量化表达**：模糊描述 → 精确数据/比例/引用支撑
- **被动与主动**：研究方法部分多用被动语态，讨论部分主动论述

#### 4.2 论证逻辑标准

- **论点-论据-论证**：每个观点必须有数据/文献/案例支撑
- **逻辑链条**：前后段落之间有明确的逻辑递进关系
- **反驳预设**：对可能的质疑提前回应（"尽管...但..."）
- **对比论证**：与已有研究对比，凸显本文贡献
- **因果严谨**：区分相关性与因果性，避免过度推断

#### 4.3 结构布局标准

- **章节衔接**：每章开头有承上启下的过渡段
- **段落结构**：主题句 → 展开 → 小结，每段聚焦一个论点
- **层次清晰**：一级标题（章）→ 二级标题（节）→ 三级标题（小节），层级不超过三级
- **摘要提升**：摘要涵盖研究背景、目的、方法、发现、贡献五要素

#### 4.4 创新贡献标准

- **显式标注**：在引言和结论中明确列出 2-3 个创新点
- **差异化表述**：用 "区别于已有研究...本文首次/创新性地..." 句式
- **理论贡献**：说明对理论框架的扩展或修正
- **实践意义**：说明对管理实践的具体指导价值

#### 4.5 文献运用标准

- **权威性**：优先引用 SSCI/CSSCI 期刊、经典著作
- **时效性**：近 5 年文献占比不低于 60%
- **对话感**：不只是罗列文献，而是与文献"对话"（"XXX(2023)指出...，本文在此基础上进一步发现..."）
- **文献综述**：按主题/流派组织，而非按时间堆砌

### Step 5: 输出

将所有润色后的章节合并，输出完整的润色后全文（markdown 格式）。

如果用户需要保存为文件，使用 Write 工具写入，文件名遵循：
`手工川-mba-thesis-polished-{YYYY-MM-DD}-v0.1.md`

## Important Notes

- **不篡改数据**：润色仅涉及表达和论证方式，不编造数据或虚构引用
- **保留原意**：所有修改必须忠实于作者原意，不改变研究结论
- **标注建议**：如果某处论证薄弱需要作者补充数据/文献，用 `[建议补充: ...]` 标注
- **分批处理**：论文通常很长，按章节分批润色，避免遗漏
