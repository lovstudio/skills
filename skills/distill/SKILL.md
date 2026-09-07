---
name: lov-distill
depends_on:
- lov-branding-consistency
description: 将真实解决过程整理为可复用经验文档并维护知识索引。支持明确输入与结果回读。Use to distill a solved problem
  into reusable knowledge.
license: MIT
compatibility: 支持 Agent Skills 的宿主；Python 3.8+ 与 PyYAML 用于 Profile 和校验。业务工具要求见工作流。
metadata:
  author: contributors
  version: 3.7.1
  content_class: authored-prose
  card_standard: lovstudio/skill-card/v1
  tags:
  - distill
  - portable-skill
---

# 经验提炼

将真实解决过程整理为可复用经验文档并维护知识索引。

## Triggers

### Activate when

- “将真实解决过程整理为可复用经验文档并维护知识索引。”
- “Distill a solved problem into reusable knowledge.”

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

1. 从当前任务及用户指定证据提取问题、根因、有效解决和适用边界。未解决问题不能写成已验证经验。

2. 从 Profile 或当前请求解析知识目录，兼容已有 distill 布局；用日期与主题命名 Markdown，保留问题、原因、解决、教训和来源。

3. 会话 ID、轮数、耗时仅取宿主实际提供的数据；不扫描其他项目的会话，不以最近文件猜当前会话，不可用时省略。

4. 维护 index.jsonl 的 date、file、title、tags、source 和可得会话字段，使用 JSON 编码防止转义错误；重复记录按源文件去重。

5. 博客同步为可选的独立发布动作。仅在请求明确包含公开同步且内容完成隐私审阅后，把精确 Markdown 路径交给可用发布能力；不得自动发布最近五篇或虚构官网链接。

6. 提交仅覆盖本次确认文件；--no-commit、--no-publish、private 始终保留。回读文档和索引，发布时单独回读实际 URL。

## Composition

执行前读取 [能力组合](references/skill-composition.md)，按明确制品交接相邻能力。

## Runtime context (shared)

运行前读取本包 `skill.yaml` 与 [Profile 合同](references/user-profile.md)。优先级为当前请求、
项目上下文、本 Skill records、共享 preferences、brand/user Profile、安全默认值。
只读取声明字段；没有专用运行时的宿主可使用 `scripts/profile_store.py` 读取共享 Profile。
配置缺失只问影响结果的一个问题。用户明确要求长期保存的值通过该脚本原子写入，
报告实际路径；不保存推断、凭据或其他任务的资料。

作者性文本执行 [作者性与来源合同](references/authorship-integrity.md)，不编造作者经历、事实或来源。
