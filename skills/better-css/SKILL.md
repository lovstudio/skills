---
name: lov-better-css
description: 清理冗余 CSS 并在现有 Tailwind 项目中重构样式。支持明确输入与结果回读。Use to refactor CSS and Tailwind
  styles.
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
  - better-css
  - portable-skill
---

# CSS 精修 · CSS Polish

清理冗余 CSS 并在现有 Tailwind 项目中重构样式。

## Triggers

### Activate when

- The user asks to use this Skill for its documented outcome.

- “清理冗余 CSS 并在现有 Tailwind 项目中重构样式。”
- “Refactor CSS and Tailwind styles.”

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

1. 读取指定样式与组件，记录动态 class、第三方约定、主题 token 和当前 Tailwind 版本。仅静态搜索无引用不能证明动态样式未使用。

2. 按重复、覆盖、未使用和可迁移样式建立修改清单；保留动画、伪元素、滚动条和必要覆盖规则。项目未采用 Tailwind 时不强行引入。

3. 逐组件合并样式并更新引用；遵循既有 semantic token，保持响应式、暗色、焦点与交互状态。用户要求 dry-run 时只交付差异方案。

4. 运行相关构建或类型检查；在可用页面对照关键断点和状态。报告实际体积变化，未测量时不填虚构百分比。

## Composition

执行前读取 [能力组合](references/skill-composition.md)，按明确制品交接相邻能力。

## Runtime context (shared)

运行前读取本包 `skill.yaml` 与 [Profile 合同](references/user-profile.md)。优先级为当前请求、
项目上下文、本 Skill records、共享 preferences、brand/user Profile、安全默认值。
只读取声明字段；没有专用运行时的宿主可使用 `scripts/profile_store.py` 读取共享 Profile。
配置缺失只问影响结果的一个问题。用户明确要求长期保存的值通过该脚本原子写入，
报告实际路径；不保存推断、凭据或其他任务的资料。
