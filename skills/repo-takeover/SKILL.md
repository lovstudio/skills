---
name: lov-repo-takeover
description: 将已有 clone 连接到用户自己的 GitHub 仓库并保留来源与历史。支持明确输入与结果回读。Use to publish a cloned
  repository under your account.
license: MIT
compatibility: 支持 Agent Skills 的宿主；Python 3.8+ 与 PyYAML 用于 Profile 和校验。业务工具要求见工作流。
depends_on:
- lov-branding-consistency
metadata:
  author: contributors
  version: 1.0.1
  content_class: deterministic-output
  card_standard: lovstudio/skill-card/v1
  tags:
  - repo-takeover
  - portable-skill
---

# 仓库接管

将已有 clone 连接到用户自己的 GitHub 仓库并保留来源与历史。

## Triggers

### Activate when

- “将已有 clone 连接到用户自己的 GitHub 仓库并保留来源与历史。”
- “Publish a cloned repository under your account.”

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

1. 读取 Git 根、分支、状态、origin、upstream 和许可，确认目标 owner/name、可见性以及用户是否要求推送。

2. 检查目标仓库是否存在和权限，已有仓库不能覆盖。保留原仓库历史与许可证，不删除 .git 或冒用原作者归属。

3. 按用户范围创建仓库，保留旧 origin 为 upstream 或明确命名的 remote；冲突时选择新 remote，不静默重置已配置目标。

4. 推送确切分支前检查敏感文件、待提交范围与远程差异，正常 hooks 与非快进保护必须保留。

5. 回读新仓库、remote 与目标提交，区分本地接管、创建、推送成功；失败时保留可恢复 remote 映射。

## Composition

执行前读取 [能力组合](references/skill-composition.md)，按明确制品交接相邻能力。

## Runtime context (shared)

运行前读取本包 `skill.yaml` 与 [Profile 合同](references/user-profile.md)。优先级为当前请求、
项目上下文、本 Skill records、共享 preferences、brand/user Profile、安全默认值。
只读取声明字段；没有专用运行时的宿主可使用 `scripts/profile_store.py` 读取共享 Profile。
配置缺失只问影响结果的一个问题。用户明确要求长期保存的值通过该脚本原子写入，
报告实际路径；不保存推断、凭据或其他任务的资料。
