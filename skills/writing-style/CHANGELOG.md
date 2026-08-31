# Changelog

## 2.5.1 - 2026-08-31

- 区分普通公众号文章与 benchmark / 实验报告的小标题策略。
- Benchmark 章节默认使用简洁的论文式描述标题，不强制制造悬念、情绪判断或金句。

## 2.5.0 - 2026-08-31

- 为 benchmark、排名、评分和雷达图文章新增方法可见性门禁。
- 要求在结果前交代输入、对照、执行 Prompt、评分 Prompt、维度设计、精确换算、单样本算分链和复现入口。
- 禁止用附件替代正文方法解释，也禁止把尚未公开的本机复现包描述为读者可用。

## 2.4.0 - 2026-08-31

- 新增读者契约与 `zero-session-context` 默认值，区分文章事实和作者与 Agent 的协作历史。
- 最终公开稿新增标题 + 开头 300 字 cold-reader hard gate。
- 禁止用悬空的“前一版 / 这次重写 / 按你的要求”向陌生读者开场。

## 2.3.0 - 2026-08-30

- make `lov-human-writing` a required pre-draft authorship and final quality gate
- remove the duplicated authorship-integrity rule copy from this Skill
- scope `lov-branding-consistency` to final audience and brand-context review

## 2.2.0 - 2026-08-30

- treat the 19-article profile as an observed repertoire instead of a mandatory article skeleton
- let structure emerge from the current material rather than defaulting to definition, distinction, and decomposition
- remove the universal human-values ending and add checks for causal compression, over-explanation, forced symmetry, and decorative counterevidence

## [2.1.0] - 2026-08-26

### Added

- 根据用户手工修订补充编辑压缩、信息层级与并列对象节奏规则。
- 明确停止重复辩护与解释梗，同时保留事实限定和证据口径。
- 补充技术枚举列表化、汇总表命名与承重句加粗的校准清单。

## [2.0.0] - 2026-08-26

### Changed

- 以 19 篇、约 12.46 万字元的 2026-08-25 实证画像重建文风规则。
- 将工作流从表面模仿升级为事实账本、题材选择、论证构建、节奏复写和防戏仿校验。
- 把技术深度、创业复盘、产品实测、个人随笔和演讲招募拆成五种适配模式。
- 移除源码中的固定个人路径和品牌词表，改由 user-profile/v1 提供运行时身份与偏好。

### Added

- 本地 style_audit.py，用于报告句长、段落、证据锚点与公关套话等可观察指标。
- User Profile 读写脚本、Skill Card、真实案例、维度地图、定价依据与分发状态。
- 相邻 Skill 组成边界和三层本地安装说明。

## [0.1.0]

- 提供基础的个人中文文风写作与改写规则。
