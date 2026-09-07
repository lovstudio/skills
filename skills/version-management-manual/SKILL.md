---
name: lov-version-management-manual
description: 生成 changeset 草稿并提供编辑入口，审阅后验证版本计划。支持明确输入与结果回读。Use to create a changeset
  for manual review.
license: MIT
compatibility: 支持 Agent Skills 的宿主；Python 3.8+ 与 PyYAML 用于 Profile 和校验。业务工具要求见工作流。
depends_on:
- lov-branding-consistency
metadata:
  author: contributors
  version: 0.1.1
  content_class: microcopy
  card_standard: lovstudio/skill-card/v1
  tags:
  - version-management-manual
  - portable-skill
---

# 版本审阅 · Version Review

生成 changeset 草稿并提供编辑入口，审阅后验证版本计划。

## Triggers

### Activate when

- “生成 changeset 草稿并提供编辑入口，审阅后验证版本计划。”
- “Create a changeset for manual review.”

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

1. 检查当前包管理器、changesets 配置、包名与实际 diff，按受影响包生成带正确 patch/minor 类型的 Markdown 草稿。

2. 展示草稿和实际文件链接，允许用户用其编辑器审阅；仅用户明确要求打开应用时才打开，不能强制前台或阻塞等待编辑器关闭。

3. 用户提供修改或确认后回读文件，用项目 changesets status 验证包名、类型和正文；同一次会话已有明确审阅授权不重复索要。

4. 该流程默认不 bump、tag 或发布；用户要求发布时交给项目既有发布流程并保留审阅后的正文。

## Composition

执行前读取 [能力组合](references/skill-composition.md)，按明确制品交接相邻能力。

## Runtime context (shared)

运行前读取本包 `skill.yaml` 与 [Profile 合同](references/user-profile.md)。优先级为当前请求、
项目上下文、本 Skill records、共享 preferences、brand/user Profile、安全默认值。
只读取声明字段；没有专用运行时的宿主可使用 `scripts/profile_store.py` 读取共享 Profile。
配置缺失只问影响结果的一个问题。用户明确要求长期保存的值通过该脚本原子写入，
报告实际路径；不保存推断、凭据或其他任务的资料。
