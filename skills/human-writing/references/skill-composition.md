# Skill Group Composition

This record is required for every generated Skill. It prevents adjacent Skills
from becoming accidental duplicates or hidden dependencies.

## Nearby Skills Inspected

按实际路由契约与输入/输出检查，不按文件名推断。检查范围是本机
本地已安装的写作、去 AI 味、公众号与润色类 Skill。

| Skill | 契约（实测） | 分类 |
|---|---|---|
| `humanizer-zh`（归藏） | 指令式。24 类 AI 写作模式的识别与改写规则，附 5 维 `/10` 主观自评表。无脚本、无可计算阈值 | **overlap** |
| `lov-anti-wechat-ai-check` | 已弃用的旧扫描实现；历史脚本可供回归，但不再作为安装入口 | archived legacy |
| `khazix-writer`（卡兹克） | 写作**生成**器：HKR 选题质检、五种文章原型、人机分工边界、个人文风内核。不做既有稿件的去 AI 味度量 | not composed（同题材，不同任务） |
| `lov-writing-style` | 依据已校准画像建立特定作者声音 | upstream/downstream atom（按阶段） |
| `lov-branding-consistency` | 检查最终可见文案的媒介、受众、品牌角色与信息可见性 | required cross-cutting gate |
| `lov-style-clone` | 从样本文章抽取文风画像，再按该画像改写 | downstream atom（可选） |
| `lov-thesis-polish` | MBA 论文提升到优秀论文水准，学术语言与论证结构 | downstream atom（可选，`thesis` 档） |
| `lov-publish-wechat-article` | 把 Markdown 写入公众号草稿箱并回读验证 | **downstream atom** |
| `lov-wechat-article-branding` | 公众号文章的目录、封面、首屏与品牌应用 | downstream atom（可选） |
| `lov-output-for-article` | 把对话输出为 `articles/` 下的文章文件 | **upstream atom**（可选） |
| `lovstudio-wxmp-cracker` | 抓取 mp.weixin.qq.com 文章正文 | upstream atom（可选） |
| `lov-write-professional-book` | 多章书稿的大纲、分章起草与全书一致性 | not composed（粒度是书，非单篇） |
| `baoyu-format-markdown` / `baoyu-markdown-to-html` | Markdown 格式化与转 HTML | not composed（排版，不涉文本特征） |

## Atomic Handoffs

交接一律以**文件**为界，不做隐式跨 Skill 调用。

| 方向 | 输入产物 | 拥有者 | 输出产物 | 验收归属 |
|---|---|---|---|---|
| upstream | 抓取或导出的 `.md` 稿件 | `lovstudio-wxmp-cracker` / `lov-output-for-article` | `./output/*.md` | 上游负责正文完整 |
| core | 原始材料 + 待改写 `.md` | **本 Skill** | 作者性账本 + 篇章报告 + 改写稿 + `--compare` | **本 Skill**：结构问题有证据、作者选择保真、表层复测完成 |
| required consumer | 事实材料 + 文风稿 | `lov-writing-style` | 带特定作者声音的稿件 | 文风 Skill 负责声音，并内置调用本 Skill 完成作者性、篇章和表层验收 |
| optional style | 作者性账本 + 草稿 | `lov-style-clone` | 带临时画像的稿件 | style-clone 负责声音；需要去 AI 味时显式调用本 Skill |
| downstream | 本 Skill 的改写稿 | `lov-publish-wechat-article` | 公众号草稿 + 回读验证 | 下游负责发布成功 |

`lov-writing-style` 的默认顺序是：先由本 Skill 建作者性账本，再完成个人文风稿，
最后回到本 Skill 做篇章与表层验收。表层指标与真实个人特征冲突时，保留作者选择
并记录理由，不能拿统计分布覆盖文风。

核心反 AI 编辑不依赖其他写作 Skill即可完整交付。`lov-branding-consistency` 是必需
横切门，但只处理最终受众和品牌语境；表内其他写作、格式与发布交接均为可选。

## Overlap Decisions

### 与 `lov-anti-wechat-ai-check`（同一 outcome，本 Skill 为升级版）

两者都要「检测 AI 痕迹 + 人性化改写」。差异是判定依据的来源：

- 旧 Skill 的阈值是手工设定的（`过渡词密度 < 15%`、`的字占比 < 5%`），文档
  未记录来源，也没有可复现的语料。
- 本 Skill 的 29 项区间全部来自 351 篇真人中文长文的实测分位数，方法、清洗
  规则与已知局限记录在 `references/benchmark.md`，可用 `--calibrate` 复现。

这个差异不是精度上的微调。本次实测发现手工阈值会在**两个方向**上错：7 项
过严（真人被误判）、4 项过松（AI 特征漏判），并且 any-fail 聚合会把 66% 的
真人稿判成 AI。手工阈值无法自查这类问题，因为它没有分布可比。

**决策：旧 Skill 退出安装发现链，不再拥有新任务路由。** 历史源可暂时保留供
回归，但“去 AI 味”“humanize”和发布前审计只发现本 Skill。

### 与 `humanizer-zh`（同一 outcome，实现形态不同）

`humanizer-zh` 的 24 类模式清单质量很高，是本 Skill 词表的重要参考来源
（否定式排比、三段式法则、破折号过度、弯引号、内联标题等指标直接对应它的
分类）。它与本 Skill 的根本差异在**验收方式**：它的收尾是一张 5 维 `/10`
主观自评表，由模型给自己打分；本 Skill 的收尾是 `--compare` 的逐项数值迁移。

前者无法回答「这次改写是否真的起了作用、有没有把别的指标推坏」——同一模型
既执行改写又评判改写，分数不构成独立证据。

**决策：本 Skill 已吸收需要的模式分类并用确定性度量验收，不再把
`humanizer-zh` 作为并列去 AI 味入口或推荐叠加链。**

### 与 `khazix-writer`（无重叠）

它解决的是「从素材写出一篇好稿」，包含选题质检与人机分工，属于创作端；本
Skill 解决「已有稿件读起来像机器」，属于修订端。两者可串联（先写后测），但
不构成重叠，也不互相依赖。

## Composition Decision

**Single Skill。**

作者性账本、篇章审计、证据约束改写和表层度量是同一个“改好并验收中文稿件”结果
的内部阶段，不应该占用四个公共触发入口。它们改为 `references/workflows/` 下的
渐进式说明，由 `lov-human-writing` 根据完整改写、只审计或只测量三种模式调度。
