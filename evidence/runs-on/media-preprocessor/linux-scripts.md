# media-preprocessor · Linux 脚本层

- 日期：2026-11-06
- 环境：Debian 12 arm64（Docker）· Python 3.12 · FFmpeg 5.1 · 无 Agent，只跑脚本
- 方式：Skill 目录只读挂载进干净容器，直接运行 Skill 自带脚本，没有 Agent，也没有联网账号
- 素材：和 macOS 运行同一批合成素材

## 结果

- 通过：探测
- 通过：分析
- 通过：技术计划
- 通过：预览渲染
- 通过：解码校验

## 说明

第一轮的 `render` 和 `photographic` 被 Skill 的门禁按设计拒绝（没做语义审核不许全片渲染，色彩未知要显式指定），改用预览渲染和显式色彩模式后通过。这里只列修正后的结果。
