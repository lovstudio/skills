# Skill Group Composition

本记录说明 `lov-algo-viz-creator` 与相邻能力的边界，避免重复造轮子或隐藏依赖。

## Nearby Skills Inspected

- **本项目的可视化引擎**（`手工川图解算法` 的 `TraceDefinition` / `SortStep` /
  `PathStep` + `TraceLab` 播放器）：这是本 Skill 概括的**核心范式来源**。
  本 Skill 把它提炼成可复用的「帧模型 + 统一播放引擎」，并产出自包含单文件
  HTML，独立于任何 React 应用。
- `frontend-design`（lovstudio）：擅长网页/界面设计输出 HTML，但目标是一般
  页面与组件，不包含「算法逐步推进的帧建模」方法与叙事规范。二者产出物可
  互不干扰。
- `lov-bp-deck` / `slide-to-pptx` / `lov-any2deck`：演示文稿/幻灯片。路线重叠
  在「用于演示」，但交付物不同：本 Skill 产出可逐步播放的交互单页，deck 产出
  静态页面流。**可选下游交接**：交互单页可被嵌入 deck 作为一页。
- `baoyu-diagram` / `lov-bp`：静态示意图/架构图。无逐步逻辑时用它们，不进入
  本 Skill。
- `hyperframes-*`（motion/animation）：逐帧动画引擎。路线相近（逐帧）但契约
  不同：hyperframes 面向 Web 关键帧动画，本 Skill 面向「算法状态变化 + 解说」，
  无硬耦合。
- `lov-repo2docs` / `document-illustrator` / `baoyu-article-illustrator`：
  文档与文章配图，不涉及逐步演示，不相邻。

## Atomic Handoffs

- **upstream → core**：算法/数据结构的概念描述与示例数据（用户或项目提供）
  → `lov-algo-viz-creator` 负责把它建模为帧序列。验收边界：`validate_viz.py` error=0。
- **core → downstream（可选）**：生成的单文件 HTML → 嵌入 deck/文章时，
  由使用者手工引用；不硬耦合任何下游 Skill。验收边界：HTML 双击可开、可播放。
- **downstream（静态图）**：用户只需要一张示意图而非逐步演示 → 明确转交
  `lov-bp` / `baoyu-diagram`，不在本 Skill 内实现。

## Overlap Decisions

- 与 `frontend-design` 无功能重叠（输出都是 HTML 但契约完全不同）。本 Skill
  的产物刻意只做演示引擎一套设计（暖学术），不需要 frontend-design 参与。
- 与 deck 类 Skill 的重叠仅限「演示」这个使用场景，交付物不同，各自独立维护。

## Composition Decision

**Single Skill**（非 Skill Kit）：一个用户可见结果（一份可播放的算法/信息
可视化 HTML），一个输入输出契约（帧模型 JSON → 自包含 HTML）。建模、校验、
生成是同一工作流的不同步骤，不是可独立触发、独立交付的模块，因此不需要
`kit.yaml` 拆分。
