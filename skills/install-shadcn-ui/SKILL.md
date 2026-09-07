---
name: lov-install-shadcn-ui
description: 安装并按项目品牌配置 shadcn/ui，保留现有主题和组件修改。支持明确输入与结果回读。Use to install and configure
  shadcn/ui for a project.
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
  - install-shadcn-ui
  - portable-skill
---

# shadcn/ui 接入

安装并按项目品牌配置 shadcn/ui，保留现有主题和组件修改。

## Triggers

### Activate when

- “安装并按项目品牌配置 shadcn/ui，保留现有主题和组件修改。”
- “Install and configure shadcn/ui for a project.”

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

1. 读取 package manager、框架、Tailwind 主版本、components.json 和现有组件；从项目品牌 token 确定主题。

2. 按当前官方安装文档选择命令，已有项目只补缺项；不固定使用旧 preset，也不因 CLI 初始化覆盖已有 CSS 和人工组件修改。

3. 配置路径别名、全局样式与 semantic token，区分 Tailwind v3 配置文件与 v4 CSS-first 方式，保留必要 reset。

4. 仅安装需求涉及的组件。对 button hover、border reset 等问题先检查实际生成代码和复现，不能无条件套用历史补丁。

5. 网络失败时才使用用户已配置代理，不写固定本机代理到通用 Skill 或 shell profile。

6. 运行构建，验证按钮状态、表单、暗色主题与响应式。输出实际新增依赖、组件和配置路径。

## Composition

执行前读取 [能力组合](references/skill-composition.md)，按明确制品交接相邻能力。

## Runtime context (shared)

运行前读取本包 `skill.yaml` 与 [Profile 合同](references/user-profile.md)。优先级为当前请求、
项目上下文、本 Skill records、共享 preferences、brand/user Profile、安全默认值。
只读取声明字段；没有专用运行时的宿主可使用 `scripts/profile_store.py` 读取共享 Profile。
配置缺失只问影响结果的一个问题。用户明确要求长期保存的值通过该脚本原子写入，
报告实际路径；不保存推断、凭据或其他任务的资料。
