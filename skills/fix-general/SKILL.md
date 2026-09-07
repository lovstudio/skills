---
name: lov-fix-general
description: 根据报错和复现证据定位根因、实施修复并验证原路径。支持明确输入与结果回读。Use to diagnose and fix a software
  error.
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
  - fix-general
  - portable-skill
---

# 故障诊疗 · Troubleshooter

根据报错和复现证据定位根因、实施修复并验证原路径。

## Triggers

### Activate when

- “根据报错和复现证据定位根因、实施修复并验证原路径。”
- “Diagnose and fix a software error.”

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

1. 读取原始错误、相关代码、配置与最近变化；先用最小复现确认现象，记录当前运行版本和环境。

2. 区分语法、依赖、配置、运行时和数据问题；按证据验证最可能原因，连续失败后重新审查假设。

3. 修改最小相关范围，不用吞异常、跳过校验、删除锁文件或降低保护掩盖问题。

4. 运行针对原缺陷的验证与受影响检查；功能依赖现有服务时复用实例，不能用静态通过替代运行结果。

5. 报告修复原因、变更、验证和剩余限制；无法完成时保留可复制错误与下一项所需证据。

## Composition

执行前读取 [能力组合](references/skill-composition.md)，按明确制品交接相邻能力。

## Runtime context (shared)

运行前读取本包 `skill.yaml` 与 [Profile 合同](references/user-profile.md)。优先级为当前请求、
项目上下文、本 Skill records、共享 preferences、brand/user Profile、安全默认值。
只读取声明字段；没有专用运行时的宿主可使用 `scripts/profile_store.py` 读取共享 Profile。
配置缺失只问影响结果的一个问题。用户明确要求长期保存的值通过该脚本原子写入，
报告实际路径；不保存推断、凭据或其他任务的资料。
