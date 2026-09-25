---
name: lov-wechat-branding-content-intelligence
description: >
  基于真实公众号文章生成标题、TOC、结构调整、摘要和可选润色计划；用于“润色标题”“生成目录”“优化文章结构”、"improve this article structure"，不直接操作编辑器。
license: MIT
depends_on:
  - lov-branding-consistency
metadata:
  author: contributors
  version: "0.2.1"
  tags:
    - content-intelligence
    - toc
    - editorial-structure
  compatibility: "Embedded module for lov-wechat-article-branding-skill."
  dependencies: []
---

# 文章结构精修 · Article Structure Editor

理解文章后生成结构化、可审阅的内容变更计划。只产出文章内容，不直接控制公众号编辑器。

## Triggers

### Activate when

- 用户要求“润色标题”“生成 TOC”“优化章节结构”“改摘要”或明确要求润色。
- Branding 管线需要从文章内容推导新增区块。
- The user asks to "improve this article structure" or generate a table of contents.

### Do not activate when

- 用户只要求封面或品牌尾注，正文结构已经稳定。
- 用户只要求把已确定内容写回页面，应交给文章访问模块。

## Workflow (MANDATORY)

1. 从文章状态提炼主题、受众、主要论点、现有章节、作者语气与发布账号身份。
2. 把输入分为文章事实、内部背景和证据缺口。
3. 单独评估标题，不把标题润色混入默认关闭的正文润色：
   - 判断文章是原创、自述、采访首发还是转载；
   - 判断当前账号是采访者、受访者还是转载者；
   - 来源媒体使用“人物名 + 评价”的第三人称标题时，受访者本人账号优先改为第一人称或主题式标题；
   - 保留文章真实核心，不为了点击率制造正文没有回答的问题。
4. 选择最小必要处理：标题、TOC、标题层级、摘要、代码或 Prompt 块、明确要求的正文润色。
5. TOC 只引用真实章节，不创造正文不存在的承诺。
6. 可复制资产使用“章节标题 + 内容块”，不补写背景和过程。
7. 正文润色时保留事实、引语、专有名词、链接、立场和信息密度；初版默认关闭正文润色。
8. 输出带锚点、唯一标记、预期文本和允许变化字段的变更计划。

## Product-manager guardrail

沟通中的人名、括号说明、私人关系、操作原因和临时判断默认只用于理解。只有读者需要的信息才进入最终文章。

## Validation

- TOC 与真实章节一一对应。
- 标题与发布账号的叙事身份一致，且得到正文和转载关系支撑。
- 新增内容不重复文章已经说明的观点。
- 代码、Prompt 或清单可以直接选择复制。
- 未启用的处理器不产生任何正文变化。

## Dependencies

None.

## Runtime context (shared)

运行前读取本 Skill 包的 `skill.yaml`，由宿主提供 `skill-runtime/v1` 上下文。字段解析顺序为：当前请求、项目上下文、个人 Preferences、品牌 Profile、通用默认值。

- 只使用 Manifest 声明的字段；Profile 保存公开品牌事实，Preferences 保存个人工作偏好。
- `required: true` 字段缺失时，按 Manifest 的问题配置向用户提出一个聚焦问题；用户明确同意后再保存回答。
- 报错提供可复制的 `context_id`、字段路径与来源，诊断内容避开秘密、完整私人路径和原始配置。
