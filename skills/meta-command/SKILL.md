---
name: lov-meta-command
description: 把重复操作封装成通用 Skill，并按需提供宿主 slash command 适配入口。支持明确输入与结果回读。Use to turn a
  repeated command workflow into a portable skill.
license: MIT
compatibility: 支持 Agent Skills 的宿主；Python 3.8+ 与 PyYAML 用于 Profile 和校验。业务工具要求见工作流。
depends_on:
- lov-branding-consistency
metadata:
  author: contributors
  version: 4.2.1
  content_class: deterministic-output
  card_standard: lovstudio/skill-card/v1
  tags:
  - meta-command
  - portable-skill
---

# 流程工坊 · Workflow Studio

把重复操作封装成通用 Skill，并按需提供宿主 slash command 适配入口。

## Triggers

### Activate when

- “把重复操作封装成通用 Skill，并按需提供宿主 slash command 适配入口。”
- “Turn a repeated command workflow into a portable skill.”

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

1. 读取用户的操作目标、输入输出与已有命令，检查相近 Skill 是否已拥有同一结果；已有能力优先扩展或复用。

2. 通用 Skill 为真源，命令文件仅是明确要求特定宿主时的薄适配。用命名输入和自然语言触发替代宿主参数插值，不重复保存两套实现。

3. 明确可重复脚本、判断流程、资源和配置边界；宿主专属模型与工具声明不进入通用核心。

4. 创建和迁移可交给已安装的 lov-skill-creator 接收原命令及输入输出合同；如不可用，按相同通用结构完成，不能执行不存在的旧插件路径。

5. 本地校验并核实安装发现性，保留原命令作为可恢复来源；官网发布仅在用户请求包含发布时交接。

## Composition

执行前读取 [能力组合](references/skill-composition.md)，按明确制品交接相邻能力。

## Runtime context (shared)

运行前读取本包 `skill.yaml` 与 [Profile 合同](references/user-profile.md)。优先级为当前请求、
项目上下文、本 Skill records、共享 preferences、brand/user Profile、安全默认值。
只读取声明字段；没有专用运行时的宿主可使用 `scripts/profile_store.py` 读取共享 Profile。
配置缺失只问影响结果的一个问题。用户明确要求长期保存的值通过该脚本原子写入，
报告实际路径；不保存推断、凭据或其他任务的资料。
