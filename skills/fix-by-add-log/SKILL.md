---
name: lov-fix-by-add-log
description: 针对难复现问题增加最少的诊断日志并用实际输出定位根因。支持明确输入与结果回读。Use to debug a problem with targeted
  logging.
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
  - fix-by-add-log
  - portable-skill
---

# 日志定位问题

针对难复现问题增加最少的诊断日志并用实际输出定位根因。

## Triggers

### Activate when

- “针对难复现问题增加最少的诊断日志并用实际输出定位根因。”
- “Debug a problem with targeted logging.”

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

1. 先读现象、复现路径和现有日志，明确待证假设及最少观测点，避免沿调用链无差别打印。

2. 在入口、分支、状态转换、外部调用及出口加统一前缀和关联 ID；仅记录必要字段，对口令、令牌、正文与用户资料做脱敏。

3. 复用当前实例复现并收集真实日志，无法自动复现时准确给出操作与需要的片段，不声称已经定位。

4. 按日志验证或否定假设，修复根因并重跑原路径；明确区分观测、推断和证实。

5. 确认问题解决后保留必要运维日志，删除本次临时调试噪声需符合用户已授权范围；原 Skill 的显式保留要求与用户不清理选择必须尊重。

## Composition

执行前读取 [能力组合](references/skill-composition.md)，按明确制品交接相邻能力。

## Runtime context (shared)

运行前读取本包 `skill.yaml` 与 [Profile 合同](references/user-profile.md)。优先级为当前请求、
项目上下文、本 Skill records、共享 preferences、brand/user Profile、安全默认值。
只读取声明字段；没有专用运行时的宿主可使用 `scripts/profile_store.py` 读取共享 Profile。
配置缺失只问影响结果的一个问题。用户明确要求长期保存的值通过该脚本原子写入，
报告实际路径；不保存推断、凭据或其他任务的资料。
