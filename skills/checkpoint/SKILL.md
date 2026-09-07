---
name: lov-checkpoint
description: 根据当前 Git 差异和历史记录保存项目里程碑及后续事项。支持明确输入与结果回读。Use to create a project checkpoint.
license: MIT
compatibility: 支持 Agent Skills 的宿主；Python 3.8+ 与 PyYAML 用于 Profile 和校验。业务工具要求见工作流。
depends_on:
- lov-branding-consistency
metadata:
  author: contributors
  version: 0.1.1
  content_class: deterministic-output
  card_standard: lovstudio/skill-card/v1
  tags:
  - checkpoint
  - portable-skill
---

# 项目存档 · Project Checkpoint

根据当前 Git 差异和历史记录保存项目里程碑及后续事项。

## Triggers

### Activate when

- “根据当前 Git 差异和历史记录保存项目里程碑及后续事项。”
- “Create a project checkpoint.”

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

1. 读取 Git 状态、暂存区、最近历史、.checkpoint_log 与项目指定记录文件。旧 Claude Code 记录可作为兼容输入，写新记录时不伪造任何宿主署名。

2. 确定上次检查点到当前的真实变化，首次运行采用存在的提交范围。记录里程碑、验证证据、未解决事项和下一步，不凭修改时间断言文档过期。

3. 在请求范围内修正与实现矛盾的 README 或配置说明，不重写仍有效内容；版本和 CHANGELOG 保持事实一致。

4. 向 .checkpoint_log 安全追加 JSONL，记录时间、项目、分支、上个哈希、变化与验证结果；项目记录默认放检查点文档，不把每次日志塞进全局 Agent 指令。

5. 用户要求检查点提交时仅暂存已核验的本次文件，检查最终暂存集合并执行正常 hooks；未授权提交时交付记录。报告日志与提交各自真实状态，重复运行避免空重复记录。

## Composition

执行前读取 [能力组合](references/skill-composition.md)，按明确制品交接相邻能力。

## Runtime context (shared)

运行前读取本包 `skill.yaml` 与 [Profile 合同](references/user-profile.md)。优先级为当前请求、
项目上下文、本 Skill records、共享 preferences、brand/user Profile、安全默认值。
只读取声明字段；没有专用运行时的宿主可使用 `scripts/profile_store.py` 读取共享 Profile。
配置缺失只问影响结果的一个问题。用户明确要求长期保存的值通过该脚本原子写入，
报告实际路径；不保存推断、凭据或其他任务的资料。
