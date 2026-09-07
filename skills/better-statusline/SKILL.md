---
name: lov-better-statusline
description: 配置并备份 Agent 状态栏，支持列出历史版本和恢复。支持明确输入与结果回读。Use to update an agent status
  line with rollback.
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
  - better-statusline
  - portable-skill
---

# 状态栏配置

配置并备份 Agent 状态栏，支持列出历史版本和恢复。

## Triggers

### Activate when

- “配置并备份 Agent 状态栏，支持列出历史版本和恢复。”
- “Update an agent status line with rollback.”

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

1. 解析 update、list、rollback 与显示内容；先识别目标应用及其实际状态栏配置。此 Skill 可由任意宿主调用，但目标应用必须提供状态栏能力。

2. 读取配置并确定字段名、输入协议与命令格式；例如 Claude Code 的 statusLine 是目标产品配置，不能把花括号示例直接当插值语法。核对当前官方协议。

3. 修改前将该字段的存在状态和值保存到用户指定备份目录；保留其他配置和秘密，备份使用不冲突的时间标识。

4. 根据真实协议实现项目路径、Git 分支、时间、分隔和颜色；脚本处理缺字段、非 Git 目录与命令失败，输出不含凭据。写配置后回读并用样例输入验证脚本。

5. list 展示版本与简短预览；rollback 先备份当前字段，再恢复所选版本，原先不存在的字段应恢复为不存在。报告配置验证与实际界面观察的区别。

## Composition

执行前读取 [能力组合](references/skill-composition.md)，按明确制品交接相邻能力。

## Runtime context (shared)

运行前读取本包 `skill.yaml` 与 [Profile 合同](references/user-profile.md)。优先级为当前请求、
项目上下文、本 Skill records、共享 preferences、brand/user Profile、安全默认值。
只读取声明字段；没有专用运行时的宿主可使用 `scripts/profile_store.py` 读取共享 Profile。
配置缺失只问影响结果的一个问题。用户明确要求长期保存的值通过该脚本原子写入，
报告实际路径；不保存推断、凭据或其他任务的资料。
