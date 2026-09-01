# Changelog

## [0.5.0] - 2026-09-01

### Added

- 建立创作战略、交互场景与标题层级的统一契约。

## [0.4.2] - 2026-09-01

### Changed

- 微信正文默认隐藏 canonical H1，文章标题只进入平台标题字段。
- 正文中的资料来源、补充链接与引申阅读默认使用低对比度的小字斜体资料注。

## [0.4.1] - 2026-09-01

### Fixed

- 将 Pillow 保留在 runtime compatibility 与文档中，不再误写进只接受 Skill ID 的 `metadata.dependencies`。

## [0.4.0] - 2026-08-31

### Changed

- 统一通过 `lov-writing-style → lov-human-writing` 处理个人文风与作者性，删除文章 Kit 的重复规则所有权。
- 将公众号品牌化合并为 `brand` 管线，并统一正文首图为 `4:3` 横向资产。
- 将忠实转载合并为 `repost` 管线，迁入来源冻结、图片账本与保真审计脚本。
- 将远端已有草稿操作路由到 `lov-publish-wechat-article`。

## [0.3.0] - 2026-08-31

### Added

- 为研究评测类公众号文章加入可复现方法链与论文式章节质量门。
- 正文首图由漂移的 3:4 竖图升级为独立的 4:3 横向资产，并保留 v1 历史包兼容校验。
- 构建文章包时复制正文引用的本地图片，并由 manifest 与质量门核对，避免本地 `prepared` 到发布预检之间丢图。

## 0.2.0

- 为公众号最终稿新增 `reader contract` 与零会话 cold-reader 门禁。
- 将旧稿轮次、用户反馈和 Agent 审稿过程明确划为内部上下文。
- 质量脚本新增标题 + 开头 300 字的会话泄漏回归测试。

## 0.1.2

- 将母品牌 `LovStudio` 与公众号发布主体 `手工川` 分开建模。
- 封面改用手工川官方白色横向 Logo lockup。
- 合成器新增白色像素比例校验，橙色和其他非白色变体直接报错。
- article/cover manifest 与质量门新增发布主体一致性检查。

## 0.1.1

- 封面品牌资产统一为发布主体官方横向 Logo lockup。
- 合成器按非透明内容框校验 Logo 宽高比，方形图标直接报错。
- cover manifest 与质量门新增横向 Logo 变体及比例回读。
- Agent Harness 案例重新生成横版封面与竖版首图。

## 0.1.0

- 创建自包含 `article-writing → editorial-template → cover-package → quality-gate` Kit。
- 固定公众号文章模板、手工川写作基线与 LovStudio Warm Academic 品牌规则。
- 输出 `2.35:1` 横版封面和 `3:4` 竖版正文首图。
- 增加文章包装、官方 Logo 合成、尺寸与 SHA-256 回读脚本。
- 以 Agent Harness System Prompt 长文完成首个真实 `prepared` 案例。
