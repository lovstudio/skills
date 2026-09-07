---
name: lov-refactor-api
description: 识别后端接口重复并在保持调用契约的前提下实施重构。支持明确输入与结果回读。Use to refactor redundant backend
  APIs.
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
  - refactor-api
  - portable-skill
---

# API 冗余整理

识别后端接口重复并在保持调用契约的前提下实施重构。

## Triggers

### Activate when

- The user asks to use this Skill for its documented outcome.

- “识别后端接口重复并在保持调用契约的前提下实施重构。”
- “Refactor redundant backend APIs.”

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

1. 识别 Tauri command、REST、GraphQL 或当前后端，列出真实接口、调用方、鉴权、参数和返回值。

2. 区分实现重复与语义不同，针对读取、CRUD、路径获取等形成候选组；不能仅因代码类似就把权限不同接口合并。

3. 先确定公共内部实现与兼容边界，必要时保留旧接口适配，避免一次修改破坏外部调用者。

4. 按依赖顺序更新服务实现和全部已知调用、类型、文档及错误处理，只有确认无使用且允许破坏兼容时移除旧入口。

5. 运行接口契约、鉴权、错误与前端调用回归，报告减少的重复及保留的兼容路径。

## Composition

执行前读取 [能力组合](references/skill-composition.md)，按明确制品交接相邻能力。

## Runtime context (shared)

运行前读取本包 `skill.yaml` 与 [Profile 合同](references/user-profile.md)。优先级为当前请求、
项目上下文、本 Skill records、共享 preferences、brand/user Profile、安全默认值。
只读取声明字段；没有专用运行时的宿主可使用 `scripts/profile_store.py` 读取共享 Profile。
配置缺失只问影响结果的一个问题。用户明确要求长期保存的值通过该脚本原子写入，
报告实际路径；不保存推断、凭据或其他任务的资料。
