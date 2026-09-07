---
name: lov-add-task
description: 在当前任务清单中按优先级和位置追加事项并保留已有状态。支持明确输入与结果回读。Use to add an item to the current
  task list.
license: MIT
compatibility: 支持 Agent Skills 的宿主；Python 3.8+ 与 PyYAML 用于 Profile 和校验。业务工具要求见工作流。
depends_on:
- lov-branding-consistency
metadata:
  author: contributors
  version: 0.1.0
  content_class: deterministic-output
  card_standard: lovstudio/skill-card/v1
  tags:
  - add-task
  - portable-skill
---

# 任务随手记 · Task Capture

在当前任务清单中按优先级和位置追加事项并保留已有状态。

## Triggers

### Activate when

- “在当前任务清单中按优先级和位置追加事项并保留已有状态。”
- “Add an item to the current task list.”

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

1. 解析任务描述、high/medium/low 优先级和 top/bottom/before/after 位置；默认 medium 和 bottom，缺描述时聚焦询问。

2. 读取宿主现有计划或任务清单，保留 ID、完成状态、负责人和已有顺序；创建唯一新 ID。

3. top/bottom 放首尾，before/after 相对当前 in_progress 项；用户明确位置优先于按高优先级自动排序。

4. 使用宿主实际提供的清单更新工具；没有时维护当前会话中可审阅的文本清单并说明保存范围，不假称数据库已更新。

5. 回读完整清单确认新项与旧状态；本操作不自动创建 Codex 独立任务、外部项目卡、提醒或给别人发送消息。

## Composition

执行前读取 [能力组合](references/skill-composition.md)，按明确制品交接相邻能力。

## Runtime context (shared)

运行前读取本包 `skill.yaml` 与 [Profile 合同](references/user-profile.md)。优先级为当前请求、
项目上下文、本 Skill records、共享 preferences、brand/user Profile、安全默认值。
只读取声明字段；没有专用运行时的宿主可使用 `scripts/profile_store.py` 读取共享 Profile。
配置缺失只问影响结果的一个问题。用户明确要求长期保存的值通过该脚本原子写入，
报告实际路径；不保存推断、凭据或其他任务的资料。
