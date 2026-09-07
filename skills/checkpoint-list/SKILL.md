---
name: lov-checkpoint-list
description: 汇总 Git 与项目日志中的检查点、时间范围和演进记录。支持明确输入与结果回读。Use to list a project checkpoint
  history.
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
  - checkpoint-list
  - portable-skill
---

# 检查点历史

汇总 Git 与项目日志中的检查点、时间范围和演进记录。

## Triggers

### Activate when

- “汇总 Git 与项目日志中的检查点、时间范围和演进记录。”
- “List a project checkpoint history.”

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

1. 只读检查当前项目的 .checkpoint_log、已配置的检查点文档以及 Git 历史。兼容旧 CLAUDE.md 和旧提交标记，同时识别通用 checkpoint 标记，不要求特定助手署名。

2. 逐行解析 JSONL，记录坏行而不把解析失败当空日志；关联时间、里程碑、分支和提交哈希，按来源去重。

3. 支持最近数量、起止日期、分支、简洁与详细视图；Git 分支和范围先校验，再作为独立参数传给命令。

4. 按真实时间排序，报告首次、最新、总数和可计算的平均间隔。日志未记录健康评分时保持未知，不补零分或虚构趋势。

5. 结果提供可追溯提交和原日志定位；该 Skill 不创建检查点、不提交或改写历史。

## Composition

执行前读取 [能力组合](references/skill-composition.md)，按明确制品交接相邻能力。

## Runtime context (shared)

运行前读取本包 `skill.yaml` 与 [Profile 合同](references/user-profile.md)。优先级为当前请求、
项目上下文、本 Skill records、共享 preferences、brand/user Profile、安全默认值。
只读取声明字段；没有专用运行时的宿主可使用 `scripts/profile_store.py` 读取共享 Profile。
配置缺失只问影响结果的一个问题。用户明确要求长期保存的值通过该脚本原子写入，
报告实际路径；不保存推断、凭据或其他任务的资料。
