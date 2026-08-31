# Skill Card — lov-human-writing

This human-readable card mirrors `skill-card.yaml`. It is a release record, not
an implementation note. A reviewer should understand the Skill without opening
its source.

## Description

先用作者性账本和七维篇章审计处理命题、因果、反例与结尾，再用 30 项中文表层
指标定位并复测。目标是保留作者选择，不是输出 AI 概率或规避平台检测。

交付物包括作者性账本、带原文证据的篇章报告、改写稿和表层数值对照。

## Owner

Lovstudio.AI（手工川工作室）· https://lovstudio.ai

## License / Terms

MIT。可自由使用、修改与再分发，保留版权声明。

内置词表参考了 `humanizer-zh` 的 AI 写作模式分类（同为 MIT）。实测分位数由
本机私人语料生成，仓库内**只包含聚合统计量，不含任何语料原文**。

## Use Case

**受众**：需要发布中文长文的写作者、公众号运营者、学术与正式文体作者。

**场景**：稿件由 AI 辅助生成或润色过，读起来「不像人写的」，需要在发布前
定位问题并改到真人文本的分布区间内。

**支持的输入**：中文 Markdown / 纯文本稿件（指标定义只对中文成立）。

**任务**：
- 建立作者性账本并审计七个篇章维度
- 度量 30 项文本特征，定位到句
- 按越界指标做定向改写（不做全文重写）
- 复测验收：改写是否生效、有没有推坏别的指标
- 基于本人历史稿件生成个人基线

## Deployment Geography

Global。本地运行，无网络调用。宿主为 Claude Code 或兼容 Agent Skills 格式的
Agent；也可直接命令行调用 `scripts/measure.py`。

## Requirements / Dependencies

- **凭据**：无。
- **Skill 依赖**：`lov-branding-consistency`，只负责最终受众与品牌语境，不参与
  AI 身份判断或作者性规则。
- **运行时**：Python 3.8+ 标准库。`scripts/measure.py` 与
  `scripts/profile_store.py` 无第三方依赖。
- **PyYAML**：仅 `scripts/validate_skill.py` 质量门需要，不影响 Skill 运行。

## Known Risks and Mitigations

| 风险 | 缓解 |
|---|---|
| 把 `fail` 误解为「检测到 AI 生成」。实际含义是「越界密度超过 90% 的真人长文」 | 报告文本、SKILL.md、README 三处显式声明不做身份判定；Step 6 禁止声称「已通过 AI 检测」 |
| 判别力（对 AI 稿的召回率）尚无带标签语料验证，可能系统性漏判 | 局限完整记录在 `references/benchmark.md` 第 5 节；被问准确率时按该节回答，不编数字 |
| 默认区间来自特定语料（2020–2026 公众号博文与访谈整理），文风差异大的用户会被系统性误判 | 提供 `--calibrate` 生成个人基线且基线自带压力标尺；四档 profile 覆盖常见文体 |
| 为凑指标写废话（把「补第一人称」做成硬塞「我觉得」） | Step 4 三条禁令：不动事实、不动立场与术语、不为凑指标写废话；Step 5 检查反向副作用 |
| 个人基线语料被 AI 生成物或口语转写污染 | `calibrate` 设 12 篇下限、低于 30 篇给出 note；benchmark.md 第 1 节记录真实污染事故与清洗规则 |
| 把虚构研究机械移植到非虚构，强行增加支线、模糊或开放结尾 | 结构修改必须回指作者性账本或原文证据；材料简单时允许线性、明确和完整 |

## References

- [Machine-readable card](skill-card.yaml)
- [Primary Skill instructions](SKILL.md)
- [阈值来源、复现方法与已知局限](references/benchmark.md)
- [作者性账本、篇章审计与非虚构边界](references/authorship-integrity.md)
- [相邻 Skill 的分工与重叠决策](references/skill-composition.md)

## Skill Output

**类型**：作者性账本、篇章审计报告、改写后的 Markdown 稿件、指标度量报告、个人基线 JSON。

**格式**：`text`（人读报告，含靶点句定位）、`json`
（`lov-human-writing/metrics/v1`）、基线 `json`
（`lov-human-writing/baseline/v1`）。

**参数**：
- `--profile` — `wechat` | `zhuque` | `neutral` | `thesis`
- `--baseline` — 个人基线路径（覆盖默认区间，并自带压力标尺）
- `--compare` — 旧版本文件，输出逐项数值迁移与状态变化
- `--calibrate` / `--out` — 从语料目录生成个人基线

**验收检查**：
- 篇章修改能回指账本或原文证据，没有制造“真人噪声”或统一价值结尾
- 改写后必须跑 `--compare`，压力分回落且无指标被反向推出界
- 事实、立场、专业术语未被改动
- 汇报中不把分布定位表述为 AI 身份判定

主产物写入 `./output/`，命名为「原文件名 + `-human-v0.x.md`」。

## Skill Version

0.3.1

## Ethical Considerations

用途是提升中文写作质量与可读性，**不是帮助伪造人类作者身份**。

不改变内容的事实性——Step 4 明确禁止新增日期、数字、人名与引语，缺细节应
向用户询问而非编造。

本工具不做「是否 AI 生成」的判定，因此**不适合用于学术诚信或平台合规的
举证**。默认阈值由私人语料生成，仓库内仅保留聚合统计量，不泄露任何个人
写作内容。

## LovStudio Evidence

### User Cases

See [`cases/cases.json`](cases/cases.json)。两个真实案例：

1. **case-01** — AI 直出稿改写：压力分 18（fail，越界 8 项）→ 3（pass，越界
   1 项），含 9 项状态迁移，并如实记录 1 项反向副作用
   （`neg_parallel_per_1k` pass→warn）。输入输出稿件均在 `cases/` 下可回读。
2. **case-02** — 351 篇误判审计：四档 profile 的真人误判率分别从
   66% / 76% / 63% / 88% 降到 9% / 7% / 7% / 7%，并记录了发现的四类 bug
   （阈值方向性错误、指标定义错误、any-fail 聚合缺陷、自校准路径重犯同一错误）。

### Dimension Map

四个命名维度见 `skill-card.yaml`：`false-positive-control`、
`rewrite-effectiveness`、`reproducibility`、`detection-recall`。

**四项 `score` 全部为 `null`，各附 `score_note` 说明原因**：前三项的证据来自
与阈值同源的语料或单个案例，同批回测出的数字不构成独立验证，打分会制造假
精度；`detection-recall` 是明确的未验证空缺——建 AI 正例集的尝试失败并已
弃用，理由记录在案，而非留空不提。

### Pricing Basis

See [`pricing-card.yaml`](pricing-card.yaml)。免费，且理由不是价值低：核心
资产是那份公开的实测分布与校准方法论，它越被复现和质疑越可靠，收费会阻碍
这件事。成本侧也支持免费——纯标准库本地脚本，无 API、无服务端、无运维。

复评触发条件：补齐带标签 AI 语料并验证出可靠召回率之后。付费产品不应把
「判别力未验证」作为已知局限交付。

### Distribution

| 渠道 | 类型 | 状态 |
|---|---|---|
| `github` | free | **planned** — 本地源已验证；远程仓库与发布交由 `lov-skill-publisher` |
| `lovstudio` | free | **planned** — 待判别力验证补齐后再上架 |
| `workbuddy` | paid | 无计划 |
| `skillpay` | paid | 无计划 |

两个免费渠道均为 planned，尚未上线。本次交付止于**本地已验证的 Skill 源**。
