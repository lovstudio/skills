# Changelog

## [0.1.1] - 2026-09-07

### Added

- 统一展示名为「算法演示台」，保持调用 ID 与能力契约。

## 0.1.0

- 初始化本地 Skill 源：帧模型规范、统一演示引擎模板、校验器与构建器。
- 帧模型 JSON（sequence/network/matrix/bars 四布局）+ `validate_viz.py` 校验 +
  `build_viz.py` 生成自包含 HTML。
- 演示引擎：播放/暂停、逐帧、变速、键盘快捷键（Space/←→/R/1/2/3）、进度条、
  中文解说条、伪代码高亮、关键直觉卡。
- 内置三个真实示例：二分查找（sequence）、拓扑排序（network）、冒泡排序（bars）。
- Lovstudio 三层 symlink 链安装（`~/.claude/skills/lov-algo-viz-creator`）。
