# WorkBuddy Connector 审核提交说明

## 提交主题

LovStudio BP Skill Kit v0.2.0（skill-only Connector）审核申请

## 项目简介

LovStudio BP Skill Kit 是一套免费、开源、可组合的商业计划书 Skill。
它将融资材料生产拆分为项目证据梳理、投资人叙事、大纲制作、PPT 生成和
专业审校几个阶段。用户既可以独立使用某一个 Skill，也可以交由总控 Skill
完成完整流程。

## 本次提交内容

- `lovstudio-bp`：识别用户意图并编排所需模块；
- `lovstudio-bp-outline`：从项目材料生成证据账本和 12–15 页 BP 大纲；
- `lovstudio-bp-deck`：将已确认大纲制作成专业融资演示文稿；
- `lovstudio-bp-polish`：审查和修正已有大纲、PPT、PDF 的证据、内容与视觉问题。

## 接入信息

- Connector ID：`lovstudio-bp`
- Connector 类型：`skill-only`
- 版本：`0.2.0`
- 最低 WorkBuddy 版本：`4.24.0`
- 认证：不需要
- 外部服务：不需要
- MCP Server：不需要
- CLI：不需要
- License：MIT
- 项目主页：https://lovstudio.ai/skills/bp
- 源代码：https://github.com/lovstudio/bp-skill

## 隐私与安全

Skill 仅处理用户主动提供或当前工作区可访问的项目材料，不要求用户提供
账号、Token、API Key 或其他第三方凭证。事实性数据与推断、假设分开记录，
生成演示文稿时禁止编造市场、财务或用户指标。

## 建议审核用例

1. “根据当前项目材料，先写一份种子轮商业计划书大纲。”
2. “把已经确认的商业计划书大纲制作成专业融资演示文稿。”
3. “逐页审查这份商业计划书，修正证据、文案和视觉问题。”
4. “从项目资料开始，完成商业计划书大纲、演示文稿和最终审校。”
