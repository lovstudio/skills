---
name: lov-architecture-documentation
description: 从项目实际实现生成架构视图、接口说明与决策记录草稿。支持明确输入与结果回读。Use to create architecture documentation
  from a codebase.
license: MIT
compatibility: 支持 Agent Skills 的宿主；Python 3.8+ 与 PyYAML 用于 Profile 和校验。业务工具要求见工作流。
depends_on:
- lov-branding-consistency
metadata:
  author: contributors
  version: 0.1.0
  content_class: authored-prose
  card_standard: lovstudio/skill-card/v1
  tags:
  - architecture-documentation
  - portable-skill
---

# 架构图谱 · Architecture Atlas

从项目实际实现生成架构视图、接口说明与决策记录草稿。

## Triggers

### Activate when

- “从项目实际实现生成架构视图、接口说明与决策记录草稿。”
- “Create architecture documentation from a codebase.”

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

1. 读取入口、manifest、服务与部署配置、API、数据 schema 和已有 docs，使用安全文件搜索代替旧命令插值。

2. 根据用户要求选择 C4、arc42、ADR、Mermaid/PlantUML 或完整文档集；文档深度服从项目复杂度，不无条件创建全部框架。

3. 记录系统边界、外部角色、容器/服务、组件职责与数据流，明确实际证据路径；未实现设计单独标作建议。

4. 描述鉴权与信任边界、质量属性、运行部署、观测与恢复事实，不把规划能力写成已上线。

5. ADR 只在有历史依据时写已决策记录，推测动机写待确认；给出未来 ADR 模板时明确草稿。

6. 生成可编辑文档与图，检查链接、语法及图与代码一致性。CI 文档发布只在请求覆盖时配置或执行。

## Composition

执行前读取 [能力组合](references/skill-composition.md)，按明确制品交接相邻能力。

## Runtime context (shared)

运行前读取本包 `skill.yaml` 与 [Profile 合同](references/user-profile.md)。优先级为当前请求、
项目上下文、本 Skill records、共享 preferences、brand/user Profile、安全默认值。
只读取声明字段；没有专用运行时的宿主可使用 `scripts/profile_store.py` 读取共享 Profile。
配置缺失只问影响结果的一个问题。用户明确要求长期保存的值通过该脚本原子写入，
报告实际路径；不保存推断、凭据或其他任务的资料。

作者性文本执行 [作者性与来源合同](references/authorship-integrity.md)，不编造作者经历、事实或来源。
