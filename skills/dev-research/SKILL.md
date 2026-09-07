---
name: lov-dev-research
depends_on:
- lov-branding-consistency
description: 根据软件需求比较复用策略并输出有来源的技术选型与研发计划。支持明确输入与结果回读。Use to research a development
  plan and technology choices.
license: MIT
compatibility: 支持 Agent Skills 的宿主；Python 3.8+ 与 PyYAML 用于 Profile 和校验。业务工具要求见工作流。
metadata:
  author: contributors
  version: 2.0.1
  content_class: authored-prose
  card_standard: lovstudio/skill-card/v1
  tags:
  - dev-research
  - portable-skill
---

# 研发选型调研

根据软件需求比较复用策略并输出有来源的技术选型与研发计划。

## Triggers

### Activate when

- “根据软件需求比较复用策略并输出有来源的技术选型与研发计划。”
- “Research a development plan and technology choices.”

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

1. 明确用户场景、技术限制、预算、时间与可检验目标；已知项直接采用，关键缺口才聚焦提问。

2. 拆分模块，对每项评估参考自研、fork 修改、库集成、混合提取和协议复用五种策略；匹配程度用实际接口与需求证据说明，不把示例百分比当测量。

3. 检索官方文档与源仓库，核实版本、维护、许可、API、部署与价格。现有单一工具能解决时直接给该方案，避免多余架构。

4. 记录选择理由、被排除方案、备用方案、模块耦合、数据流、MVP 阶段、风险与成本假设。每个重要事实给出处与日期。

5. 输出到用户指定位置或项目 output 目录的研发计划，并说明实施验收；该调研不自行安装、采购或部署。

## Composition

执行前读取 [能力组合](references/skill-composition.md)，按明确制品交接相邻能力。

## Runtime context (shared)

运行前读取本包 `skill.yaml` 与 [Profile 合同](references/user-profile.md)。优先级为当前请求、
项目上下文、本 Skill records、共享 preferences、brand/user Profile、安全默认值。
只读取声明字段；没有专用运行时的宿主可使用 `scripts/profile_store.py` 读取共享 Profile。
配置缺失只问影响结果的一个问题。用户明确要求长期保存的值通过该脚本原子写入，
报告实际路径；不保存推断、凭据或其他任务的资料。

作者性文本执行 [作者性与来源合同](references/authorship-integrity.md)，不编造作者经历、事实或来源。
