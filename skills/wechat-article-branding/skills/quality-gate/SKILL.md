---
name: lov-wechat-branding-quality-gate
description: >
  验收公众号文章的内容、结构、审美、品牌准确性与保存持久化；用于“检查最终效果”“保存后验证”、"review the branded WeChat article"，并修复发现的问题。
license: MIT
depends_on:
  - lov-branding-consistency
metadata:
  author: contributors
  version: "0.4.2"
  tags:
    - quality-gate
    - editorial-review
    - regression-check
  compatibility: "Embedded module; browser preview is required for live acceptance."
  dependencies: []
---

# 品牌文章验收 · Branded Article Review

以读者可见结果和真实平台状态验收文章。除非用户明确只要报告，发现问题后直接修复并重新检查。

## Triggers

### Activate when

- Branding 管线进入最终验收或用户说“检查最终效果”“保存后确认一下”。
- 用户明确请求只读 `audit`。
- The user asks to "review the branded WeChat article" or verify the saved result.

### Do not activate when

- 上游还没有产出完整候选内容或封面。
- 用户只需要生成素材文件，不需要文章级验收。

## Workflow (MANDATORY)

1. 读取 `$KIT_DIR/references/acceptance.md`。
2. 比较文章原始快照、变更计划和当前页面状态。
3. 检查内容命题、事实、引语、链接和作者语气。
4. 检查文章标题是否匹配发布账号身份与转载关系，并检查正文首屏、TOC、章节标题、封面 Prompt、代码块、品牌区的顺序、数量与层级。
5. 检查封面横版、方形裁切、正文首屏、焦点和 Logo 完整性；确认 Logo 来自 `publication.logo` 且与 `publication.name` 一致。
6. 检查品牌名称、产品承诺、URL、品牌色和禁止公开内容；确认品牌主体未借正文隐喻临时发挥，品牌尾注没有自动枚举无关产品；经正文相关性或用户请求选中的产品只展示一个 `products[].url` 主链接。
7. 启用 `cover_prompt` 时，检查公开 Prompt 可复制、只出现一次、不含本地路径、内部备注或虚假复现方式。
8. 检查测试文字、空壳节点、重复图片和非目标字段变化。
9. 保存并重新加载，再执行一次关键检查。
10. `audit` 管线只报告；其他管线修复根因后重复验收。

## Completion rule

以下状态均不等于完成：本地生成成功、上传完成、选择成功、DOM 已变化、页面出现成功提示。只有目标结果在真实预览中成立，并在保存后重载仍存在，才可以报告完成。

## Output

- 已观察到的文章状态；
- 运行的管线和模块；
- 计划内变化与保持不变的字段；
- 横版、方形和正文检查结果；
- 未运行或仍缺证据的能力。

## Dependencies

Authenticated browser preview and the before/after article state from the article-access module.

## Runtime context (shared)

运行前读取本 Skill 包的 `skill.yaml`，由宿主提供 `skill-runtime/v1` 上下文。字段解析顺序为：当前请求、项目上下文、个人 Preferences、品牌 Profile、通用默认值。

- 只使用 Manifest 声明的字段；Profile 保存公开品牌事实，Preferences 保存个人工作偏好。
- `required: true` 字段缺失时，按 Manifest 的问题配置向用户提出一个聚焦问题；用户明确同意后再保存回答。
- 报错提供可复制的 `context_id`、字段路径与来源，诊断内容避开秘密、完整私人路径和原始配置。
