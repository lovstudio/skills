# lov-human-writing

![Version](https://img.shields.io/badge/version-0.3.1-CC785C)

先确认哪些问题、判断、取舍和未决处真正属于作者，再审整篇如何组织因果、反例与
结尾，最后才量出 30 项中文表层指标并复测。目标是保住作者性，不是逃过检测。

## 为什么不是又一个「去 AI 味」提示词

同类方案给的是模式清单（该删哪些套话）或手工阈值（过渡词密度 < 15%）。它们
都无法回答同一个问题：**这次改写到底有没有生效，有没有把别的地方改坏。**

因为执行改写和评判改写是同一个模型，自评分不构成独立证据。

表层改写的验收仍使用确定性度量。一次真实的改写记录（`cases/cases.json`
case-01）：

```
总判定 fail -> pass      压力分 18 -> 3      越界项 8 -> 1

句长变异系数 CV          0.452 -> 0.657   fail -> pass
段落长度变异系数         0.22  -> 0.818   fail -> pass
一句成段占比             0.0   -> 0.417   fail -> pass
分句尾「体现/彰显了…」   1.16  -> 0.0     fail -> pass
数字串（个/千字）        0.0   -> 28.95   fail -> pass
「的」字占比             0.044 -> 0.0274  fail -> pass
否定式排比               1.16  -> 1.56    pass -> warn   ← 副作用，照实记录
```

最后一行是重点：改写会有副作用，工具要能把它显示出来，而不是只报喜。

## 阈值从哪来

不是拍脑袋。351 篇真人中文长文（约 169 万字）的实测分位数，方法与清洗规则见
[`references/benchmark.md`](references/benchmark.md)。

这一步推翻了初版的手工阈值，而且错在两个方向：7 项过严（句首重复率上限设
0.10，真人中位数其实是 0.29）、4 项过松（四字格套话真人 p90 就是 0，却给了
0.5 的余量）。还有两项指标的**定义**就是错的——按出现总数数破折号和弯引号，
可中文正规写法本就用「——」和成对引号。

更关键的是聚合逻辑：原实现 29 项设区间的指标里任何一项越界即判 fail，而按 p10/p90 定界
每项本身带约 10% 的设计内尾部概率，`1 - 0.9²⁹ ≈ 95%`。实测真人语料 66% 被
判 fail，但 fail 项数中位数只有 1——单项越界是定界噪声，不是文本问题。改成
累计压力分之后：

| profile | 真人判 fail 率 |
|---|---|
| wechat | 66% → 9% |
| zhuque | 76% → 7% |
| neutral | 63% → 7% |
| thesis | 88% → 7% |

## 它不做什么

**不判断一篇文章是否由 AI 生成。** `fail` 的准确含义是「越界密度超过 90% 的
真人长文」。判别侧（对 AI 稿的召回率）尚无带标签语料验证，局限记录在
`references/benchmark.md` 第 5 节。

不要用它做学术诚信或平台合规的举证。

它也不会为了“像人”故意加入错别字、口头禅、无关支线、开放结尾或虚构经历。
篇章审计只修改能够回指原文和作者性账本的问题。

## 一个入口，四个内部阶段

本仓库只安装和发现 `lov-human-writing`。完整流程内部拆成四个阶段：

1. `authorship-ledger`：记录作者问题、判断、亲历、删留决定、反例和禁编项；
2. `discourse-audit`：审命题来源、因果压缩、反例存活、收束压力和读者推理空间；
3. `editorial-rewrite`：按证据做最小结构编辑，不套统一“人味”模板；
4. `surface-audit`：运行 30 项中文指标与 `--compare`。

这些阶段位于 `references/workflows/`，不再作为独立 Skills 暴露。完整契约见
[`references/authorship-integrity.md`](references/authorship-integrity.md)。

## 本地安装

```bash
npx skills add lovstudio/human-writing-skill -g -y
```

本地真源安装：

在本仓库根目录执行：

```bash
export SKILL_SOURCE_DIR="$(pwd)"
mkdir -p "${SKILL_SKILLS_INSTALL_DIR:?请设置本地 Skills 目录}"
ln -s "$SKILL_SOURCE_DIR" "$SKILL_SKILLS_INSTALL_DIR/lov-human-writing"
```

## 使用

### 例一：改一篇 AI 味重的公众号稿

```bash
# 1. 先建立作者性账本并审计整篇结构
# 2. 再度量表层压力分与靶点句
python3 scripts/measure.py -i draft.md -p wechat

# 3. 按篇章证据与越界指标定向改写

# 4. 重跑篇章审计，再复测表层指标
python3 scripts/measure.py -i draft-v2.md -p wechat --compare draft.md
```

档位按编辑场景选：`wechat`（公众号，默认）、`zhuque`（高强度表层审计）、
`neutral`（通用非虚构）、`thesis`（学术正式，禁 emoji、收紧加粗）。这些档位
只改变编辑阈值，不对应任何平台检测器。

### 例二：用自己的文风建个人基线

默认阈值来自一批公开中文长文，不是你本人的文风。有 ≥ 30 篇本人手写稿件时：

```bash
python3 scripts/measure.py --calibrate ~/writing/ --out baseline.json
python3 scripts/measure.py -i draft.md -b baseline.json -p wechat
```

基线会自带压力标尺（区间和标尺必须同源，否则等于用别人的尺子量自己）。

语料必须是**本人手写**的——混入 AI 生成物或口语转写会污染基线。
`references/benchmark.md` 第 1 节记录了一次真实的污染事故：669 篇初筛样本里
有 315 篇是生成物、转写稿或技术文档搬运。

## 用户 Profile（跨 session）

`skill.yaml` 声明 `user-profile/v1`，从共享 Profile 读取用户、品牌、工作区与
本 Skill 的长期记录。本 Skill 持久化两项：

- `records.default_profile` — 常用档位
- `records.baseline_path` — 个人基线路径（最重要的一项）

用户直接说出的持久偏好由 `scripts/profile_store.py` 写回，源代码保持可移植。
详见 [`references/user-profile.md`](references/user-profile.md)。

## 原子组合

[`references/skill-composition.md`](references/skill-composition.md) 记录已检查
的相邻 Skill、重叠决策与可选交接。要点：

- `lov-anti-wechat-ai-check` 已收敛为旧命令兼容入口；新任务统一路由到本 Skill。
- 文风类 Skill 提供画像与作者声音；本 Skill 的作者性账本必须在成文前建立，表层
  度量则在文风成形后运行。指标与真实个人风格冲突时保留作者选择。
- 反 AI 编辑流程不依赖其他写作 Skill；唯一横切依赖 `lov-branding-consistency`
  只负责最终受众与品牌语境。`lov-writing-style` 可以把本 Skill 作为必经成稿门。

## 可信度卡与用户案例

- `skill-card.yaml` / `skill-card.md` — 用途、负责人、风险、输出与维度地图
- `cases/cases.json` — 两个真实案例（AI 稿改写、351 篇误判审计）
- `pricing-card.yaml` — 免费的理由、交付边界与复评触发条件

维度地图里 `detection-recall`（对 AI 稿的召回率）明确记为未验证空缺，不给分。
四个维度的 `score` 全部为 `null` 并附 `score_note` 说明为何不打分——同批语料
回测出的数字不构成独立验证。

## 质量门

```bash
python3 scripts/validate_skill.py .
```

## 依赖

- `lov-branding-consistency`：只处理最终可见文案的媒介、受众与品牌语境，不接管
  作者性、反 AI 规则或正文观点。
- Python 3.8+ 标准库。`scripts/measure.py` 与 `scripts/profile_store.py` 无
  第三方依赖。
- PyYAML — **仅** `scripts/validate_skill.py` 质量门需要，不影响 Skill 运行。

## License

MIT。内置词表参考了 `humanizer-zh` 的 AI 写作模式分类（同为 MIT）。实测分位数
由私人语料生成，仓库内只含聚合统计量，不含任何语料原文。
