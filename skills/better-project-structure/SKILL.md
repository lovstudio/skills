---
name: lov-better-project-structure
description: 分析任意语言项目的目录职责并渐进调整文件结构和引用。支持明确输入与结果回读。Use to improve a project directory
  structure.
license: MIT
compatibility: 支持 Agent Skills 的宿主；Python 3.8+ 与 PyYAML 用于 Profile 和校验。业务工具要求见工作流。
depends_on:
- lov-branding-consistency
metadata:
  author: contributors
  version: 2.0.1
  content_class: deterministic-output
  card_standard: lovstudio/skill-card/v1
  tags:
  - better-project-structure
  - portable-skill
---

# 项目结构整理

分析任意语言项目的目录职责并渐进调整文件结构和引用。

## Triggers

### Activate when

- “分析任意语言项目的目录职责并渐进调整文件结构和引用。”
- “Improve a project directory structure.”

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

1. 读取 manifest、入口、构建配置、测试与 Git 状态，识别语言、框架、单包或 monorepo。项目现有约定优先，不按固定文件数或目录深度判定质量。

2. 建立文件职责与依赖图，定位混合职责、重复结构、命名冲突和散落的测试。给出最小迁移映射，支持 minimal、verbose 与仅分析模式。

3. 先处理低耦合移动，再模块化；同时更新 import、构建路径、测试发现、文档和资源引用。已有 .projectstructure.yaml 只作为用户配置读取，不把示例伪代码当作已实现工具。

4. 清理前区分源码、构建产物、缓存和用户备份，删除需明确范围，优先可恢复归档；不因文件被忽略就删除 node_modules 或运行中目录。

5. 运行实际构建与相关测试，逐项回读引用，输出新目录、修改清单与可恢复路径；不虚构健康分、交互界面或性能收益。

## Composition

执行前读取 [能力组合](references/skill-composition.md)，按明确制品交接相邻能力。

## Runtime context (shared)

运行前读取本包 `skill.yaml` 与 [Profile 合同](references/user-profile.md)。优先级为当前请求、
项目上下文、本 Skill records、共享 preferences、brand/user Profile、安全默认值。
只读取声明字段；没有专用运行时的宿主可使用 `scripts/profile_store.py` 读取共享 Profile。
配置缺失只问影响结果的一个问题。用户明确要求长期保存的值通过该脚本原子写入，
报告实际路径；不保存推断、凭据或其他任务的资料。
