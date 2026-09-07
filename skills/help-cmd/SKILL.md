---
name: lov-help-cmd
description: 把操作目标转换为适合当前系统和 shell 的可执行命令说明。支持明确输入与结果回读。Use to create a command line
  for a task.
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
  - help-cmd
  - portable-skill
---

# 需求转命令

把操作目标转换为适合当前系统和 shell 的可执行命令说明。

## Triggers

### Activate when

- “把操作目标转换为适合当前系统和 shell 的可执行命令说明。”
- “Create a command line for a task.”

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

1. 解析目标、输入输出与是否要求执行，识别操作系统、shell、工具版本和当前目录。

2. 优先已有可靠 CLI，以安全引用处理空格、中文、通配符和用户参数。macOS BSD、Linux GNU、Windows PowerShell 语法分别核对。

3. 给出最短有效命令及关键参数含义，必要时提供可复制的多步流程；不以隐藏命令替换执行用户文本。

4. 只问命令时保持只读；请求包含执行时遵守实际目标与权限边界，先确认破坏性对象，不根据命令示例扩大授权。

5. 检查工具 help 或官方文档，明确缺少依赖与未运行状态。

## Composition

执行前读取 [能力组合](references/skill-composition.md)，按明确制品交接相邻能力。

## Runtime context (shared)

运行前读取本包 `skill.yaml` 与 [Profile 合同](references/user-profile.md)。优先级为当前请求、
项目上下文、本 Skill records、共享 preferences、brand/user Profile、安全默认值。
只读取声明字段；没有专用运行时的宿主可使用 `scripts/profile_store.py` 读取共享 Profile。
配置缺失只问影响结果的一个问题。用户明确要求长期保存的值通过该脚本原子写入，
报告实际路径；不保存推断、凭据或其他任务的资料。
