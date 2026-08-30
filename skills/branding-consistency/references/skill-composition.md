# Skill Group Composition

## Nearby Skills Inspected

- `lov-writing-style`：按已校准的个人文风完成长文、改写或诊断。它拥有“像谁写”和
  题材适配，不拥有任意界面组件的受众、品牌角色与可见性边界。
- `humanizer-zh`：删除 AI 套话、公式结构与机械节奏。它能改善自然度，但不会决定
  Caption 是否应存在、按钮在失败状态该承担什么任务。
- `lov-anti-wechat-ai-check`：面向公众号平台风险检测模板短语和结构。它的验收目标
  是 AI 痕迹，不是跨媒介语境适配。
- `copywriting`：面向营销页面的价值主张、异议处理、证明与转化。它是网站营销场景
  的可选上游，不适合 App 状态、出版 Caption 或策划案决策语言的统一验收。
- `lov-article-creator`：建立公众号事实账本、文章结构与视觉包。它可交接文章 Markdown
  与组件清单；本 Skill 负责其中标题、Caption、CTA、品牌尾注等可见文案的在位审校。
- `lov-output-for-article` 与 `lov-publish-wechat-article`：分别负责文件落盘和公众号草稿
  写入，不拥有文案判断。文案规则变化后需要新的外部发布授权。

## Atomic Handoffs

1. 可选上游：writing-style、copywriting 或 article creator 输出草稿、组件清单与品牌
   Profile。上游验收事实、结构或转化策略；本 Skill 从用户可见文本开始。
2. 核心：`lov-branding-consistency` 接收原文、目标 surface/component、受众与品牌上下文，
   输出可直接使用的文案或删除决策；验收包括语境、可见性、品牌、组件惯例与事实。
3. 可选下游：humanizer 或 anti-AI 能力接收已经通过语境验收的长文，输出自然度或
   平台风险报告；不得重新加入内部元话语或改变品牌角色。
4. 可选下游：文件输出、设计、App 实现或公众号发布能力消费最终文本。它们只负责
   落位与渠道状态，修改文案后必须重新经过本 Skill 的在位验收。

## Overlap Decisions

- 与 writing-style 的共同点是调整语言；前者追求稳定个人声音，本 Skill 追求具体场景
  的受众与品牌适配，两者可串联但不能互相替代。
- 与 humanizer、anti-AI 的共同点是删除模型痕迹；本 Skill 处理更上游的叙述位置和
  信息边界，即使一句话没有套话，也可能因为暴露“正文首图”“官方 Logo”而失败。
- 与 copywriting 的共同点是考虑受众；copywriting 拥有营销转化，本 Skill 覆盖营销
  之外的出版、产品、方案与视觉组件，并负责跨场景一致的可见性门禁。
- 不扩展任何现有 Skill，因为这些能力的 routing 与最终验收均不同。

## Composition Decision

这是 Single Skill。生成、改写、审校和删除决策共享同一份 context contract、可见性
防火墙与质量门，构成一个用户结果；`copy_audit.py` 只是辅助诊断，不拥有独立交付。
所有 sibling Skill 均通过文本、brief、Profile 或报告交接。凡会输出读者可见文本的
LovStudio Skill，必须在其 frontmatter 的 `depends_on` 中显式声明
`lov-branding-consistency`；依赖清单由 `references/dependent-skills.yaml` 管理并验证。
