# Changelog

## 0.3.1 - 2026-09-01

### Fixed

- 补齐 `0.3.0` 入口已经引用、但官网发布仓库缺失的作者性契约与四个 progressive-disclosure workflow 文件。

## 0.3.0 - 2026-08-30

### Changed

- collapse the four discoverable Kit modules into internal progressive-disclosure workflows
- expose only `lov-human-writing` as the anti-AI writing entrypoint
- define calibrated personal voice as protected input when invoked by `lov-writing-style`

## 0.2.0 - 2026-08-30

### Added

- add a self-contained four-module Skill Kit: authorship ledger, discourse audit, evidence-bound rewrite, and surface audit
- add `authorship-integrity/v1` guidance for thesis provenance, causal compression, counterevidence, closure pressure, reader inference, structural asymmetry, and author decision trace
- add explicit `full`, `audit`, and `surface-only` pipelines

### Changed

- move surface metrics to the final validation layer instead of treating them as the whole anti-AI workflow
- prohibit invented human noise, universal value endings, AI probability claims, and platform-passing promises
- route legacy `lov-anti-wechat-ai-check` work to this Skill

## 0.1.0

首个本地已验证版本。

### 核心

- `scripts/measure.py` — 30 项中文文本指标的确定性度量 CLI（纯标准库）：
  节奏 / burstiness、模板与重复、结构规整度、具体性与立场、机械指纹五族。
  支持四档 profile（`wechat` / `zhuque` / `neutral` / `thesis`）、靶点句定位、
  `--compare` 版本对照、`--calibrate` 个人基线生成。
- `SKILL.md` — 度量 → 定向改写 → 复测验收的完整工作流，含指标到改法的映射表。

### 阈值校准

默认区间由 351 篇真人中文长文（约 169 万字）的实测分位数确定，取代初版手工
阈值。语料清洗规则、完整分位数表、双向定界规则与已知局限见
`references/benchmark.md`。

校准过程中修掉四类问题：

- **阈值方向性错误**：7 项过严（`opener_repeat_ratio` 上限设 0.10，真人中位数
  实为 0.29 / p90 0.49；另含 `colon_per_1k`、`bold_per_1k`、`heading_per_1k`、
  `first_person_per_1k`、`rule_of_three_per_1k`、`solo_para_ratio`），4 项过松
  （`idiom4_per_1k`、`hedge_per_1k`、`de_ratio`、`sent_len_cv`）。
- **指标定义错误**：`em_dash_count` / `curly_quote_count` 按出现总数计数，而
  中文正规写法本就使用「——」与成对引号，从定义上注定误判真人。改为
  `lone_dash_per_1k`（孤立单破折号，英文排版惯性）与 `quote_style_mixed`
  （引号体系混用数）。`emoji_count` 改为 `emoji_per_1k` 以消除长度偏差。
- **聚合逻辑缺陷（主要根因）**：`overall()` 原为 any-fail——29 项设区间的指标任一越界即判
  fail。按 p10/p90 定界每项本身带约 10% 的设计内尾部概率，取并集即
  `1 - 0.9²⁹ ≈ 95%`；实测真人语料 66% 被判 fail，而 fail 项数中位数仅为 1。
  改为累计压力分（fail 记 2 分、warn 记 1 分），与**同 profile** 真人压力分布
  比较；`PROFILE_PRESSURE` 按档位分别校准，避免把档位偏移误报为文本失败。
  家族级 rollup 同步改为压力阈值，不再 any-fail。
- **自校准路径重犯同一错误**：`calibrate()` 用 p25/p75 做 target 而主逻辑用
  p10/p90，导致用户以自身 40 篇稿件校准后回测同一批，57% 被判 fail。统一为
  `target=p10/p90, warn=p05/p95`，并让基线自带 `pressure_reference`——区间与
  标尺必须同源。同时处理 p90 退化为 0 的情形（退回默认近零上界），新增 12 篇
  样本量下限与低于 30 篇的 note。

真人误判率结果：`wechat` 66%→9%、`zhuque` 76%→7%、`neutral` 63%→7%、
`thesis` 88%→7%；个人基线路径 57%→5%。

### 其他调整

- `latin_per_1k` 降级为信息项（不设区间）：英文 token 密度取决于选题，不是
  人机信号，保留区间只贡献误判。
- 报告尾部输出压力分与真人基准分位数，并显式声明本引擎只做分布定位、不做
  「是否 AI 生成」的身份判定。

### 证据

- `cases/cases.json` — 两个真实案例：AI 直出稿改写（压力分 18→3，越界 8→1，
  含 1 项反向副作用如实记录）、351 篇误判审计。输入输出稿件在 `cases/` 下可回读。
- `references/skill-composition.md` — 邻近 Skill 群检查结论：与
  `lov-anti-wechat-ai-check`（手工阈值）、`humanizer-zh`（模式清单 + 主观自评）
  为同一 outcome 的不同实现，均保留作对比基线；文风类 Skill 必须在本 Skill
  之后运行。判定为 Single Skill。
- `skill-card.yaml` / `skill-card.md` / `pricing-card.yaml` — 四个命名维度的
  `score` 均为 `null` 并附不打分理由；`detection-recall` 明确记为未验证空缺。

### 已知局限

- 校准后的 7–9% 不是独立验证结果：阈值与判定标尺均取自同一批语料，同批回测
  得到约 10% 的 fail 率是定义使然，仅证明实现与设计意图一致。
- 判别力（对 AI 稿的召回率）无带标签语料验证。建 AI 正例集的尝试失败并已
  弃用——以 `output/` 目录作启发式抓到的 49 篇中大量为人写的发言稿、公关稿与
  大纲表格，且与真人集反向污染，基于它的分离度数字不成立。
