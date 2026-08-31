# Skill composition

## Nearby Skills Inspected

`lov-writing-style` 是可选上游；`lov-dev-blog` 面向网站博客；`lov-anti-wechat-ai-check` 是可选下游诊断。

## Atomic Handoffs

本模块接收事实材料，输出 Markdown 草稿给 `lov-editorial-template`。验收边界是命题、证据和第一人称成立。

## Overlap Decisions

内嵌最小文风基线，不硬依赖外部文风 Skill；后者只在用户单独维护文风 Profile 时调用。

## Composition Decision

作为自包含 Kit 的内容上游随源码分发，不独立上架，也不把检测分数当成写作目标。
