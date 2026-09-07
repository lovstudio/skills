---
name: lov-version-management
description: 根据实际包变更生成 changeset，并按请求更新版本与 CHANGELOG。支持明确输入与结果回读。Use to manage package
  versions with Changesets.
license: MIT
compatibility: 支持 Agent Skills 的宿主；Python 3.8+ 与 PyYAML 用于 Profile 和校验。业务工具要求见工作流。
depends_on:
- lov-branding-consistency
metadata:
  author: contributors
  version: 2.0.1
  content_class: microcopy
  card_standard: lovstudio/skill-card/v1
  tags:
  - version-management
  - portable-skill
---

# Changesets 版本管理

根据实际包变更生成 changeset，并按请求更新版本与 CHANGELOG。

## Triggers

### Activate when

- The user asks to use this Skill for its documented outcome.

- “根据实际包变更生成 changeset，并按请求更新版本与 CHANGELOG。”
- “Manage package versions with Changesets.”

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

1. 读取包管理器、workspace、包名、版本、changesets 配置、待发布记录与 Git diff。缺少配置时按当前官方流程初始化，保留项目已有发布方式。

2. 默认 add：按实际行为为每个受影响的非忽略包选择 patch 或 minor，写唯一 .changeset Markdown，frontmatter 用真实包名，正文写用户能理解的变化。

3. 支持 monorepo 一条 changeset 多包，检查内部依赖与 private 包策略；不能从文件路径直接推断全部发布范围。

4. status：执行项目 changesets status 并解释待发布版本，保持只读。manual 审阅可交接稿件，不假定特定宿主编辑器。

5. release 仅在用户明确请求时运行 version，回读 package 版本、lockfile 与 CHANGELOG，提交精确文件后走项目发布 CI。已有 0.x 默认保持 0.x，不能自动升到 1.0。

6. 不以文件截断的 YAML 示例替代完整流程，不覆写已发 tag，不把生成 changeset 报为已发布。

## Composition

执行前读取 [能力组合](references/skill-composition.md)，按明确制品交接相邻能力。

## Runtime context (shared)

运行前读取本包 `skill.yaml` 与 [Profile 合同](references/user-profile.md)。优先级为当前请求、
项目上下文、本 Skill records、共享 preferences、brand/user Profile、安全默认值。
只读取声明字段；没有专用运行时的宿主可使用 `scripts/profile_store.py` 读取共享 Profile。
配置缺失只问影响结果的一个问题。用户明确要求长期保存的值通过该脚本原子写入，
报告实际路径；不保存推断、凭据或其他任务的资料。
