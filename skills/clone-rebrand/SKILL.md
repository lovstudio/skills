---
name: lov-clone-rebrand
description: 将模板或 fork 改造为新项目，按范围同步品牌、语言和部署设置。支持明确输入与结果回读。Use to create a project
  from a template and rebrand it.
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
  - clone-rebrand
  - portable-skill
---

# 项目换装 · Project Makeover

将模板或 fork 改造为新项目，按范围同步品牌、语言和部署设置。

## Triggers

### Activate when

- “将模板或 fork 改造为新项目，按范围同步品牌、语言和部署设置。”
- “Create a project from a template and rebrand it.”

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

1. 读取模板许可、原 upstream、Git 状态、项目配置与当前品牌；从请求获取新名称和描述，仅询问必要的归属或部署目标。

2. 按包名、显示名、组件、文档、资源、i18n 分类建立替换映射，区分代码标识符和用户文案。保留许可证、来源归属、存储兼容键及历史迁移。

3. 实施本地重塑，同步 import、路由、环境变量名和实际存在的 Logo 引用；凭据值不复制，备份与用户改动不覆盖。

4. 检查目标 GitHub 组织和可见性；只有请求包含新仓库与推送时创建并推送，保留上游地址。不能把原 origin 静默覆盖，也不批量暂存无关文件。

5. 仅在请求包含部署时使用当前项目的发布流程，域名需有真实配置和回读；最终分别报告本地重塑、仓库、部署和 DNS 状态。

## Composition

执行前读取 [能力组合](references/skill-composition.md)，按明确制品交接相邻能力。

## Runtime context (shared)

运行前读取本包 `skill.yaml` 与 [Profile 合同](references/user-profile.md)。优先级为当前请求、
项目上下文、本 Skill records、共享 preferences、brand/user Profile、安全默认值。
只读取声明字段；没有专用运行时的宿主可使用 `scripts/profile_store.py` 读取共享 Profile。
配置缺失只问影响结果的一个问题。用户明确要求长期保存的值通过该脚本原子写入，
报告实际路径；不保存推断、凭据或其他任务的资料。
