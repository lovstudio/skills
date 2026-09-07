---
name: lov-code-review
description: 审查实际差异中的正确性、安全和维护风险并给出可定位意见。支持明确输入与结果回读。Use to review a code change for
  actionable defects.
license: MIT
compatibility: 支持 Agent Skills 的宿主；Python 3.8+ 与 PyYAML 用于 Profile 和校验。业务工具要求见工作流。
depends_on:
- lov-branding-consistency
metadata:
  author: contributors
  version: 0.1.0
  content_class: deterministic-output
  card_standard: lovstudio/skill-card/v1
  tags:
  - code-review
  - portable-skill
---

# 代码审阅官 · Code Reviewer

审查实际差异中的正确性、安全和维护风险并给出可定位意见。

## Triggers

### Activate when

- “审查实际差异中的正确性、安全和维护风险并给出可定位意见。”
- “Review a code change for actionable defects.”

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

1. 读取明确范围的 diff、相关调用与项目规则；无范围时检查当前变更，不假定审查整个仓库。

2. 优先检查可复现缺陷、输入边界、权限、秘密、错误处理、状态、副作用及性能退化，结合调用上下文判断。

3. 区分真正影响行为的问题和风格偏好，不把通用检查清单当成已发现缺陷；必要时运行有针对性的只读验证。

4. 按严重度给具体文件行号、触发条件、后果和修复建议；没有可行动问题时如实说明，不凑发现。

5. 审查默认不改代码、不提交、不发送 review 评论；用户要求修复时再按范围实施。

## Composition

执行前读取 [能力组合](references/skill-composition.md)，按明确制品交接相邻能力。

## Runtime context (shared)

运行前读取本包 `skill.yaml` 与 [Profile 合同](references/user-profile.md)。优先级为当前请求、
项目上下文、本 Skill records、共享 preferences、brand/user Profile、安全默认值。
只读取声明字段；没有专用运行时的宿主可使用 `scripts/profile_store.py` 读取共享 Profile。
配置缺失只问影响结果的一个问题。用户明确要求长期保存的值通过该脚本原子写入，
报告实际路径；不保存推断、凭据或其他任务的资料。
