---
name: lov-article-creator
description: >
  统一创建、改写、品牌化或忠实转载微信公众号文章包：正文写作调用唯一文风与作者性能力，离线完成结构、品牌、封面、4:3 首图、来源与质量验收。Use when asked to write, brand, audit, or faithfully repost a WeChat article package.
license: MIT
compatibility: "Portable Agent Skills format; Python 3.9+, PyYAML and Pillow for deterministic packaging and cover composition."
depends_on:
  - lov-branding-consistency
  - lov-writing-style
metadata:
  author: LovStudio
  version: "0.4.1"
  card_standard: lovstudio/skill-card/v1
  tags:
    - wechat
    - article-writing
    - editorial-system
    - branded-cover
  dependencies: []
---

# lov-article-creator

把零散事实、研究材料或现有草稿变成一套可交付的公众号文章包，而不只是写出一段 Markdown。

每次完整交付同时包含：经过事实约束的正文、题材适配的编辑模板、品牌化横版封面、独立的 `4:3` 横向正文首图、来源与发布元数据，以及一份可回读的验收报告。

## Triggers

### Activate when

- “按我的文风写一篇公众号文章，并配好封面和正文首图。”
- “把这些研究材料做成统一品牌的公众号长文。”
- “Create a branded WeChat article package from these notes.”
- “Turn this draft into a publish-ready WeChat article with a wide cover and a 4:3 body hero.”
- “把这篇现有 Markdown 做成完整的品牌化公众号版本。”
- “忠实转载这篇合作方文章，保留原文并加入我们的开场和收尾。”

### Do not activate when

- 只要求改写一段文字或匹配个人语气，不需要公众号模板与视觉包；使用写作风格能力。
- 只要求读取、修改或核验公众号后台已有草稿；使用 `lov-publish-wechat-article` 的 existing-draft 管线。
- 只要求把现成文件写入草稿箱或正式发布；使用公众号发布能力。
- 只要求生成一张孤立图片，且不需要文章级命题、品牌与双比例验收。

## Product contract

- **One article, one package.** 正文、来源、封面、首图和验收记录位于同一文章目录。
- **Facts before voice.** 先建立事实账本，再套用文风；不得用第一人称补造经历、数字或判断变化。
- **One writing owner.** 新写与改写必须调用 `lov-writing-style`；其内部调用唯一的反 AI / 作者性规则源 `lov-human-writing`。本 Skill 只拥有公众号题材、结构、品牌和制品规则，不复制通用文风规则。
- **Template is semantic.** 固定的是信息顺序、证据门槛与品牌组件，不强迫所有题材使用同一组空洞标题。
- **Brand comes from Profile.** 发布主体、Logo、官网、色彩和禁用信息从共享 Profile 解析，不把用户私有路径写入公开文章或 Skill 源码。
- **Two image roles are mandatory.** 完整管线必须输出 `2.35:1` 分享封面和独立的 `4:3` 横向正文首图；不得把分享封面成品直接当正文首图。
- **Benchmark claims require benchmark evidence.** 文章一旦给出排名、雷达图或量化优劣，就必须在结果之前公开测试对象、输入、完整 Prompt、执行环境、评价指标、评分规则、至少一个逐项算分示例和复现方法；分数不得先于方法出现。
- **Publication identity wins.** 公众号发布主体与母品牌分开；封面只使用发布主体官方白色横向 lockup，方形图标、母品牌 Logo 和橙色变体都不能替代。
- **Generated is not accepted.** 文件存在不等于完成；必须通过尺寸、引用、事实、品牌和移动阅读质量门。
- **Publishing is separate.** 默认止于本地可发布文章包；写入草稿箱或正式发布需要明确授权，并交给下游发布能力。
- **Repost source is frozen.** 转载时来源正文是逐字冻结区；作者性优化只作用于发布方新增区块，且 `copyrightMode` 固定为 `reprint`。

## User Profile

每次运行先读取 `skill.yaml` 声明的 `user-profile/v1` 上下文，按当前请求、项目事实、本 Skill records、共享 preferences、品牌和用户 Profile、安全默认值的顺序解析。

用户直接声明并希望长期沿用的模板、文风、品牌与封面比例，通过 `scripts/profile_store.py record --confirm` 写入 `skills.lov-article-creator.records`。公开品牌事实使用 `brand.*`；推断值、凭据和内部素材不得持久化。

## Skill Kit Modules

完整执行前读取 `kit.yaml` 与所选模块：

- `$SKILL_DIR/skills/article-writing/SKILL.md` — 事实账本、题材结构，以及对 `lov-writing-style` 的正文写作交接。
- `$SKILL_DIR/skills/editorial-template/SKILL.md` — 固定公众号模板、品牌组件和文章包元数据。
- `$SKILL_DIR/skills/cover-package/SKILL.md` — 艺术方向、横版封面、4:3 正文首图和确定性 Logo 合成。
- `$SKILL_DIR/skills/quality-gate/SKILL.md` — 内容、文风、品牌、图片和包结构验收。

模块是本 Kit 的硬依赖并随源代码分发。外部相邻 Skill 只通过明确文件交接，不是隐藏依赖。

## Pipelines

| 管线 | 适用结果 | 模块 |
| --- | --- | --- |
| `full` | 从材料生成完整文章包 | writing → template → cover → quality |
| `rewrite` | 把已有草稿重做为统一公众号版本 | writing → template → quality |
| `visual` | 正文已定，只补双比例视觉包 | cover → quality |
| `brand` | 给现有本地文章补齐结构、品牌、封面说明与双比例视觉 | template → cover → quality |
| `repost` | 冻结来源正文，只新增发布方开场、来源标注、收尾与品牌区 | template → cover → repost audit → quality |
| `audit` | 只检查现有文章包 | quality |

用户说“写公众号文章”且没有显式缩小范围时，默认使用 `full`。

## Workflow (MANDATORY)

### Step 0: Resolve the Kit and durable defaults

1. 定位 Skill 根目录，检查 `kit.yaml`、所需模块、references、scripts 和 assets。
2. 读取共享 Profile 与 `skills.lov-article-creator.records`。
3. 分别解析母品牌和公众号发布主体，并读取发布主体官方白色横向 Logo、品牌网站、文风、横竖比例和输出目录；不得回退到母品牌、方形或橙色 Logo。
4. 缺失的信息会改变用户可见成品时，只问一个聚焦问题；其余使用安全默认值继续。

### Step 1: Build the truth ledger

完整读取输入文件、当前项目材料、图片和用户明确判断，内部区分：

- 可直接写入的事实、版本、数字、引用和链接；
- 可以使用第一人称的真实经历；
- 需要来源支撑的外部主张；
- 只帮助判断、不得公开的内部上下文；
- 会阻止可靠成稿的证据缺口。

把文章真正要纠正的旧说法或推动的判断压成一句命题。输入不足以支撑关键结论时，保留边界或请求最少事实，不编造完整故事。

同时建立 `reader contract`：发布渠道、目标读者、读者打开文章时已知内容和成品边界。
公众号最终稿默认面对没有参加作者与 Agent 对话的公开读者。旧稿轮次、用户批评、
修改说明和任务过程属于内部上下文；除非它们本身是研究对象并在正文内完整建立，
不得进入文章命题或导语。

### Step 2: Write for meaning

读取文章写作模块，并把 truth ledger、reader contract、题材和发布渠道交给 `lov-writing-style`。`lov-writing-style` 负责个人文风，并在内部调用 `lov-human-writing` 做作者性审计；不得绕过这条链路另写一套“去 AI 味”规则。

公众号专属结构继续执行：

1. 开头 300 字内出现真实冲突、现场、结果或核心判断。
2. 把标题与开头 300 字单独交给 `zero-session-context` 冷读者；所有版本、人物、事件和
   指代都必须在可见成品中有先行词。出现悬空的“前一版 / 上一稿 / 这次重写 / 按你
   的要求”时直接重写，不能进入下一阶段。
3. 正文优先按定义、区分、证据、代价与行动推进。
4. 每个主要章节至少有一项事实、案例、数字、亲历或来源。
5. 长句承担解释，短句负责落锤；保持移动端一句段与长段交替。
6. 先完成事实与论证，再做个人文风适配；不复制口头禅，不制造虚假情绪。
7. 先判断题材。研究、调研、对比测试、benchmark 或带排名/雷达图的文章使用论文式方法结构：`调研对象`、`测试方法`、`Prompt`、`评价指标`、`评分方法`、`评分示例`、`复现方法`、`测试结果`、`局限性`、`结论`。这些标题以检索和复现为先，保持朴素，不强行改成悬念句或判断句。
8. 研究评测类文章在 `测试结果` 前必须让读者看见：被测版本或散列、统一输入、实际执行 Prompt、模型与关键参数、隔离条件、样本数与重复次数、盲评或随机化方式、指标定义和权重、逐项评分示例、可运行命令与原始产物索引。缺一项就只能写“探索性观察”，不能给确定排名。

`repost` 管线不改写来源正文。完整读取 [来源保真](references/repost-source-fidelity.md)、[转载增量](references/repost-editorial-overlay.md) 与 [作者性边界](references/repost-authorship-integrity.md)，把来源放入唯一 `data-repost-source="true"` 冻结区；只把新增开场、来源标注、收尾和品牌微文案交给写作链路。

### Step 3: Apply the editorial template

读取 `$SKILL_DIR/references/article-template.md` 与编辑模板模块，将正文装入固定语义结构：

1. 标题与发布元数据；
2. `4:3` 横向正文首图；
3. 导语；
4. 正文与必要的 TOC；
5. 结论或“写在最后”；
6. 有真实去向时加入代码、原文、博客或延伸阅读；
7. 稳定品牌尾注；
8. 结论之后、品牌尾注之前的封面说明：真实艺术作品写“本期封面”，生成式封面写可复制的“封面 Prompt”；
9. `read_original_url`、来源和发布字段。

用 `scripts/build_article_package.py` 建立目录和 manifest。不得为了填满模板创造不存在的链接、产品或作者经历。

现有文章使用 `brand` 管线时，额外读取 [品牌化版本](references/brand-edition.md)。`publication`、`brand` 与 `products` 必须分开；品牌尾注默认不枚举产品，只有与正文直接相关或用户明确要求时才加入。

### Step 4: Produce the cover package

读取 `$SKILL_DIR/references/cover-system.md`、`$SKILL_DIR/prompts/cover-art.md` 与封面模块：

1. 从文章命题提取一个主视觉隐喻，不使用机器人、代码 UI、霓虹、科技粒子或伪文字凑“AI 感”。
2. 生成不含 Logo、标题、字母、数字和水印的艺术底图，分别为分享封面和正文首图保留安全区。
3. 使用同一视觉语言分别构图分享封面和 `4:3` 正文首图；不要复用已叠 Logo 的分享封面成品，也不要机械拉伸。
4. 运行 `scripts/compose_covers.py`，使用发布主体官方白色横向 raster Logo 确定性合成并输出 PNG、JPG 与 manifest；脚本必须拒绝方形和非白色 Logo。
5. 分享封面用于公众号消息列表；`4:3` 正文首图位于正文第一块、导语之前。

### Step 5: Run the quality gate

读取 `$SKILL_DIR/references/quality-gate.md`，运行：

```bash
python3 "$SKILL_DIR/scripts/validate_article_package.py" \
  --package ARTICLE_PACKAGE \
  --json
```

同时做人工语义检查：事实与引语、作者位置、文风节奏、标题与摘要、延伸阅读、品牌主体、封面焦点、Logo 完整性和正文首图移动阅读效果。研究评测类文章还必须逐项核对实验输入、Prompt、环境、评分规则、原始结果与复现入口。`audit` 只报告；其他管线发现问题后直接修复并重跑。

转载包还必须运行：

```bash
python3 "$SKILL_DIR/scripts/audit_repost.py" \
  --source-text SOURCE_TEXT \
  --edition-html EDITION_HTML \
  --source-account SOURCE_ACCOUNT \
  --source-url SOURCE_URL \
  --copyright-mode reprint
```

### Step 6: Deliver the package

默认输出到当前工作区 `output/articles/<slug>/`：

```text
article.md
article-manifest.json
sources.md
cover/
  art-master.png
  wechat-cover-wide.png
  wechat-cover-wide.jpg
  article-opening-4x3.png
  article-opening-4x3.jpg
  cover-manifest.json
quality-report.json
```

`repost` 管线另外输出来源快照、`source-assets/`、`edition-manifest.json` 和保真审计收据；远端 Lovpen HTML 与发布收据由 Publisher 生成。

报告事实支持范围、实际文件、使用的 Profile 来源和验证结果。未获授权时，不创建公众号草稿、不正式发布、不发送外部消息。

## Dependencies

- Python 3.9+、PyYAML、Pillow。
- 完整封面需要宿主提供图像生成或合法素材输入；确定性合成本身不需要网络。
- `lov-writing-style` 是正文文风的唯一外部 owner；其作者性审计由 `lov-human-writing` 内置完成。
- 发布和公众号后台编辑属于下游 `lov-publish-wechat-article`，不属于本 Skill 的默认交付。

## References

- [文章模板](references/article-template.md)
- [写作风格](references/writing-style.md)
- [品牌系统](references/brand-system.md)
- [封面系统](references/cover-system.md)
- [输出契约](references/output-contract.md)
- [质量门](references/quality-gate.md)
- [品牌化版本](references/brand-edition.md)
- [转载来源保真](references/repost-source-fidelity.md)
- [转载编辑增量](references/repost-editorial-overlay.md)
- [转载发布交接](references/repost-publication-handoff.md)
- [转载作者性边界](references/repost-authorship-integrity.md)
- [Skill 组合](references/skill-composition.md)
