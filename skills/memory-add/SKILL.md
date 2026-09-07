---
name: lov-memory-add
description: 将用户指定信息保存为带分类、标签和来源的知识文档及索引。支持明确输入与结果回读。Use to save a knowledge note
  with categories and tags.
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
  - memory-add
  - portable-skill
---

# 知识记录

将用户指定信息保存为带分类、标签和来源的知识文档及索引。

## Triggers

### Activate when

- “将用户指定信息保存为带分类、标签和来源的知识文档及索引。”
- “Save a knowledge note with categories and tags.”

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

1. 从请求解析信息、标题、分类、标签和来源，目录由 Profile 或明确路径确定；兼容已有 memory/index.jsonl。

2. 读取相关已有记录，防止重复或冲突；URL 资料先获取真实内容，不能只凭标题生成事实。

3. 生成简洁 Markdown，包含必要内容、用法示例、相关来源与记录日期；个人信息仅在授权知识库内保存，凭据不进入正文或索引。

4. 使用不冲突文件名写入，并以 JSON 编码追加 index.jsonl 的 date、file、title、category、tags、source；写入前备份或原子更新。

5. 回读正文和索引，报告确切路径及归类，不自动发布知识或提交其他修改。

## Composition

执行前读取 [能力组合](references/skill-composition.md)，按明确制品交接相邻能力。

## Runtime context (shared)

运行前读取本包 `skill.yaml` 与 [Profile 合同](references/user-profile.md)。优先级为当前请求、
项目上下文、本 Skill records、共享 preferences、brand/user Profile、安全默认值。
只读取声明字段；没有专用运行时的宿主可使用 `scripts/profile_store.py` 读取共享 Profile。
配置缺失只问影响结果的一个问题。用户明确要求长期保存的值通过该脚本原子写入，
报告实际路径；不保存推断、凭据或其他任务的资料。
