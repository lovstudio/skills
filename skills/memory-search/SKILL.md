---
name: lov-memory-search
description: 跨已配置的 memory 与 distill 知识记录检索并返回可追溯结果。支持明确输入与结果回读。Use to search a personal
  knowledge base.
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
  - memory-search
  - portable-skill
---

# 知识寻回 · Knowledge Finder

跨已配置的 memory 与 distill 知识记录检索并返回可追溯结果。

## Triggers

### Activate when

- “跨已配置的 memory 与 distill 知识记录检索并返回可追溯结果。”
- “Search a personal knowledge base.”

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

1. 从明确路径或 Profile 解析知识库范围，兼容 memory 与 distill 子目录；缺少目录时报告未配置，不全盘搜索私人文件。

2. 解析关键词、分类、标签、时间、精确或模糊匹配，先搜索 JSONL 索引，再按需全文检索 Markdown。

3. 使用安全文本匹配处理中文、标点和 shell 字符，坏索引行单独记录；检索失败与零结果分开。

4. 按相关度返回标题、匹配摘要、来源类型、日期和真实文件链接，不把截断片段补写成原文。

5. 只在用户选定或结果需要时读完整文档；不因搜索而修改、上传或重建知识库。

## Composition

执行前读取 [能力组合](references/skill-composition.md)，按明确制品交接相邻能力。

## Runtime context (shared)

运行前读取本包 `skill.yaml` 与 [Profile 合同](references/user-profile.md)。优先级为当前请求、
项目上下文、本 Skill records、共享 preferences、brand/user Profile、安全默认值。
只读取声明字段；没有专用运行时的宿主可使用 `scripts/profile_store.py` 读取共享 Profile。
配置缺失只问影响结果的一个问题。用户明确要求长期保存的值通过该脚本原子写入，
报告实际路径；不保存推断、凭据或其他任务的资料。
