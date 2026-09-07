---
name: lov-init-port
description: 为项目选择稳定开发端口并更新实际框架启动配置。支持明确输入与结果回读。Use to configure a stable development
  port.
license: MIT
compatibility: 支持 Agent Skills 的宿主；Python 3.8+ 与 PyYAML 用于 Profile 和校验。业务工具要求见工作流。
depends_on:
- lov-branding-consistency
metadata:
  author: contributors
  version: 1.1.1
  content_class: deterministic-output
  card_standard: lovstudio/skill-card/v1
  tags:
  - init-port
  - portable-skill
---

# 端口初始化 · Port Setup

为项目选择稳定开发端口并更新实际框架启动配置。

## Triggers

### Activate when

- “为项目选择稳定开发端口并更新实际框架启动配置。”
- “Configure a stable development port.”

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

1. 读取项目名、已有端口约定、package scripts、框架配置与正在监听的端口。已有可用且稳定配置优先保留。

2. 无既定端口时使用原规则：按字符位置从 1 起加权 Unicode 码点求和，再对 6000 取余加 3000，即 3000 + sum(ord(c) * (i + 1) for i, c in enumerate(project_name)) % 6000；结果只是候选，不能宣称天然唯一。

3. 检测候选冲突并选可用端口，记录最终值，不终止其他进程或抢占监听。

4. Next.js 在实际 dev 命令配置 -p；Vite 更新 server.port；其他框架依据当前支持方式设置，不能只写可能不被读取的环境变量。

5. 保持项目既有环境文件与参数，不启动第二实例；回读配置并在允许运行验证时确认监听地址。

## Composition

执行前读取 [能力组合](references/skill-composition.md)，按明确制品交接相邻能力。

## Runtime context (shared)

运行前读取本包 `skill.yaml` 与 [Profile 合同](references/user-profile.md)。优先级为当前请求、
项目上下文、本 Skill records、共享 preferences、brand/user Profile、安全默认值。
只读取声明字段；没有专用运行时的宿主可使用 `scripts/profile_store.py` 读取共享 Profile。
配置缺失只问影响结果的一个问题。用户明确要求长期保存的值通过该脚本原子写入，
报告实际路径；不保存推断、凭据或其他任务的资料。
