---
name: lov-brainstorm
description: 通过证据和聚焦追问明确需求、约束、取舍及验收条件。支持明确输入与结果回读。Use to help clarify requirements
  through brainstorming.
license: MIT
compatibility: 支持 Agent Skills 的宿主；Python 3.8+ 与 PyYAML 用于 Profile 和校验。业务工具要求见工作流。
depends_on:
- lov-branding-consistency
metadata:
  author: contributors
  version: 1.0.1
  content_class: authored-prose
  card_standard: lovstudio/skill-card/v1
  tags:
  - brainstorm
  - portable-skill
---

# 需求梳理

通过证据和聚焦追问明确需求、约束、取舍及验收条件。

## Triggers

### Activate when

- “通过证据和聚焦追问明确需求、约束、取舍及验收条件。”
- “Help clarify requirements through brainstorming.”

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

1. 先读用户已有背景与项目资料，提取起因、现状、目标和边界，不重复询问已知信息。

2. 找出会改变结果的歧义或矛盾，一次问一个具体问题；量化快、更好、简单等模糊要求。区分用户事实与自己的假设，不为了追问而追问。

3. 按产品、缺陷或技术决策场景讨论用户任务、复现证据、替代方案、依赖、成本和可恢复性；保持中立，不暗示预选答案。

4. 信息足够即收敛为需求、约束、优先级、未决问题与可检验成功条件。讨论本身不授权实现、发布或创建外部任务。

## Composition

执行前读取 [能力组合](references/skill-composition.md)，按明确制品交接相邻能力。

## Runtime context (shared)

运行前读取本包 `skill.yaml` 与 [Profile 合同](references/user-profile.md)。优先级为当前请求、
项目上下文、本 Skill records、共享 preferences、brand/user Profile、安全默认值。
只读取声明字段；没有专用运行时的宿主可使用 `scripts/profile_store.py` 读取共享 Profile。
配置缺失只问影响结果的一个问题。用户明确要求长期保存的值通过该脚本原子写入，
报告实际路径；不保存推断、凭据或其他任务的资料。

作者性文本执行 [作者性与来源合同](references/authorship-integrity.md)，不编造作者经历、事实或来源。
