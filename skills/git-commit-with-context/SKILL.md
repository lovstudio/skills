---
name: lov-git-commit-with-context
description: 结合会话意图与实际 Git 差异生成并执行范围准确的提交。支持明确输入与结果回读。Use to create a Git commit for
  the current task changes.
license: MIT
compatibility: 支持 Agent Skills 的宿主；Python 3.8+ 与 PyYAML 用于 Profile 和校验。业务工具要求见工作流。
depends_on:
- lov-branding-consistency
metadata:
  author: contributors
  version: 1.1.1
  content_class: microcopy
  card_standard: lovstudio/skill-card/v1
  tags:
  - git-commit-with-context
  - portable-skill
---

# 会话提交 · Context Commit

结合会话意图与实际 Git 差异生成并执行范围准确的提交。

## Triggers

### Activate when

- “结合会话意图与实际 Git 差异生成并执行范围准确的提交。”
- “Create a Git commit for the current task changes.”

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

1. 从会话建立候选文件与变更目的，再检查 git status、未暂存差异和暂存差异验证候选集合；会话记忆不能代替当前状态。

2. 保留其他任务的暂存内容，同文件混合改动按 hunk 审阅；不能分离时先交付明确差异，不批量覆盖或清空暂存区。

3. 采用项目既有 Conventional Commits 约定，根据实际行为选 feat、fix、docs、refactor 等；默认简洁中文，重要原因放正文。

4. 用户要求提交时只暂存核验文件或 hunk，提交前再次确认暂存集合；正常运行 hooks，不使用跳过检查参数，不伪造 Co-Authored-By。

5. 回读提交哈希、文件和 message，确认原有无关改动保留。仅生成 message 请求不执行 commit；推送另需在请求范围内。

## Composition

执行前读取 [能力组合](references/skill-composition.md)，按明确制品交接相邻能力。

## Runtime context (shared)

运行前读取本包 `skill.yaml` 与 [Profile 合同](references/user-profile.md)。优先级为当前请求、
项目上下文、本 Skill records、共享 preferences、brand/user Profile、安全默认值。
只读取声明字段；没有专用运行时的宿主可使用 `scripts/profile_store.py` 读取共享 Profile。
配置缺失只问影响结果的一个问题。用户明确要求长期保存的值通过该脚本原子写入，
报告实际路径；不保存推断、凭据或其他任务的资料。
