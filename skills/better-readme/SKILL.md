---
name: lov-better-readme
depends_on:
- lov-branding-consistency
description: 依据项目代码完善 README、安装说明、使用示例与真实品牌资产。支持明确输入与结果回读。Use to create or improve
  a project README.
license: MIT
compatibility: 支持 Agent Skills 的宿主；Python 3.8+ 与 PyYAML 用于 Profile 和校验。业务工具要求见工作流。
metadata:
  author: contributors
  version: 2.9.1
  content_class: authored-prose
  card_standard: lovstudio/skill-card/v1
  tags:
  - better-readme
  - portable-skill
---

# README 精修 · README Polish

依据项目代码完善 README、安装说明、使用示例与真实品牌资产。

## Triggers

### Activate when

- “依据项目代码完善 README、安装说明、使用示例与真实品牌资产。”
- “Create or improve a project README.”

### Do not activate when

- 只是查询本 Skill 的说明，或请求与上述结果无关的任务；不执行实际业务操作。
- 用户仅要预览或审查时，不进入修改、提交或发布分支。

## Execution boundary

自然语言请求即可触发；无需旧 slash 路径、参数插值或指定助手。明确解析当前请求中的
项目、目标文件、选项与输出位置；用当前宿主实际提供的文件、搜索、CLI 和浏览器能力。
项目依赖版本与外部 API 在执行时核实，不能假设示例是现行配置。随包脚本从 Skill 根解析，
业务文件从目标项目根解析。先读当前状态，保护已有未提交内容与其他任务的暂存区。
分析、预览请求保持只读；修改、提交、推送、部署和发布各依当前请求的明确范围执行。
不绕过保护、自动发送消息、强制结束用户进程或抢前台。失败保留可诊断原始错误。

## Workflow

1. 读取现有 README、manifest、入口、实际 scripts、许可与远程仓库；保留已有有效内容和用户改动。根 README 写仓库级信息，单项功能细节放相应文档并链接。

2. 用一句话说明用途，再给真实可执行的安装、快速开始、主要功能、使用示例、技术栈与许可。只有实际支持时列快捷键、平台、下载与截图。

3. 保留现有封面和 Logo。需要补图时使用当前可用生成能力，封面可放 docs/images/cover.png；品牌从 Profile 或项目资产解析，不硬编码色值。已有资产不因优化文案而自动重画。

4. 可使用同排 32px Logo 和 h1、strong 简介及平台 sub 文本；GitHub 会限制样式，优先普通 Markdown 与支持的 HTML 属性。修复所有本地图片和锚点链接，不添加占位图服务。

5. 从项目 LICENSE 读取许可；缺失时说明未声明，不能擅自授予 Apache 或其他许可。仅公开仓库且有展示价值时添加已核验 owner/repo 的 Star History。

6. 验证文档命令、路径与版本；提交和推送仅在请求包含这些动作时执行，使用本次确切文件清单，不 squash 已发布历史。

## Composition

执行前读取 [能力组合](references/skill-composition.md)，按明确制品交接相邻能力。

## Runtime context (shared)

运行前读取本包 `skill.yaml` 与 [Profile 合同](references/user-profile.md)。优先级为当前请求、
项目上下文、本 Skill records、共享 preferences、brand/user Profile、安全默认值。
只读取声明字段；没有专用运行时的宿主可使用 `scripts/profile_store.py` 读取共享 Profile。
配置缺失只问影响结果的一个问题。用户明确要求长期保存的值通过该脚本原子写入，
报告实际路径；不保存推断、凭据或其他任务的资料。

作者性文本执行 [作者性与来源合同](references/authorship-integrity.md)，不编造作者经历、事实或来源。
