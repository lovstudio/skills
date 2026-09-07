---
name: lov-kb-organize
description: 检查并整理知识库索引、重复文档、图片位置和内部引用。支持明确输入与结果回读。Use to organize a knowledge base
  and its references.
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
  - kb-organize
  - portable-skill
---

# 知识库管家 · Knowledge Organizer

检查并整理知识库索引、重复文档、图片位置和内部引用。

## Triggers

### Activate when

- “检查并整理知识库索引、重复文档、图片位置和内部引用。”
- “Organize a knowledge base and its references.”

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

1. 从请求或 Profile 定位知识库，解析 scan、archive、dedup、reorg、images、lint 和目标范围；默认为 scan。

2. scan 检查目录、文档、图片与断链；dedup 以标题和内容相似度定位候选，不把相似度阈值当删除依据，也不自动合并。

3. archive 将明确目标移至有日期的归档目录，保留相对路径与可恢复映射。reorg 按明确的源→目标移动，防止覆盖同名文件。

4. images 根据当前库约定整理附件，更新相对 Markdown 与现有 wiki 链接；处理 fragment、空格和 URL 编码，不误改外链。

5. lint 检查标题、元数据和引用约定，实际备份不能假定编辑工具自动保存历史。

6. 修改后重新检查所有受影响引用与索引，报告修复和剩余候选；不自动提交整个知识库。

## Composition

执行前读取 [能力组合](references/skill-composition.md)，按明确制品交接相邻能力。

## Runtime context (shared)

运行前读取本包 `skill.yaml` 与 [Profile 合同](references/user-profile.md)。优先级为当前请求、
项目上下文、本 Skill records、共享 preferences、brand/user Profile、安全默认值。
只读取声明字段；没有专用运行时的宿主可使用 `scripts/profile_store.py` 读取共享 Profile。
配置缺失只问影响结果的一个问题。用户明确要求长期保存的值通过该脚本原子写入，
报告实际路径；不保存推断、凭据或其他任务的资料。
