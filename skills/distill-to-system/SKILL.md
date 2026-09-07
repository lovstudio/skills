---
name: lov-distill-to-system
description: 把有证据的可复用经验写入最合适的项目或共享 Agent 规范。支持明确输入与结果回读。Use to persist a reusable
  lesson in agent instructions.
license: MIT
compatibility: 支持 Agent Skills 的宿主；Python 3.8+ 与 PyYAML 用于 Profile 和校验。业务工具要求见工作流。
depends_on:
- lov-branding-consistency
metadata:
  author: contributors
  version: 1.0.1
  content_class: microcopy
  card_standard: lovstudio/skill-card/v1
  tags:
  - distill-to-system
  - portable-skill
---

# 经验写入规则

把有证据的可复用经验写入最合适的项目或共享 Agent 规范。

## Triggers

### Activate when

- “把有证据的可复用经验写入最合适的项目或共享 Agent 规范。”
- “Persist a reusable lesson in agent instructions.”

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

1. 解析待保存经验及适用范围，先定位当前项目规范、领域 reference 或目标 Skill，避免把局部问题扩大为全局规则。

2. 读取目标并检查重复、冲突和优先级；对时效性的 API 或工具事实先查证，保留来源与生效时间。

3. 将触发条件、正确动作、边界写成一到三行可执行规则，放在最窄 canonical 层。直接用户要求保存才持久化，推断仅作为建议。

4. 保留编号、链接和版本约定，按项目要求更新 CHANGELOG 并验证宿主链接。禁止硬编码作者主目录、密钥和未经核实的弃用日期。

5. 回读新增规则并报告确切目标；不把本地规范修改自动发布到远程。

## Composition

执行前读取 [能力组合](references/skill-composition.md)，按明确制品交接相邻能力。

## Runtime context (shared)

运行前读取本包 `skill.yaml` 与 [Profile 合同](references/user-profile.md)。优先级为当前请求、
项目上下文、本 Skill records、共享 preferences、brand/user Profile、安全默认值。
只读取声明字段；没有专用运行时的宿主可使用 `scripts/profile_store.py` 读取共享 Profile。
配置缺失只问影响结果的一个问题。用户明确要求长期保存的值通过该脚本原子写入，
报告实际路径；不保存推断、凭据或其他任务的资料。
