---
name: lov-xbti-gallery
license: MIT
compatibility: Requires `gh` CLI for listing cases.
description: 从已核实的社区地址或仓库列出可访问的 XBTI 人格测试案例。支持明确输入与结果回读。Use to browse a gallery of
  XBTI personality tests.
depends_on:
- lov-branding-consistency
metadata:
  author: contributors
  version: 1.0.3
  tags:
  - bti
  - personality-test
  - gallery
  - xbti
  content_class: deterministic-output
  card_standard: lovstudio/skill-card/v1
---

# XBTI 案例浏览

从已核实的社区地址或仓库列出可访问的 XBTI 人格测试案例。

## Triggers

### Activate when

- “从已核实的社区地址或仓库列出可访问的 XBTI 人格测试案例。”
- “Browse a gallery of XBTI personality tests.”

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

1. 从用户请求、项目配置或 Profile 获取 gallery URL 或 repository；旧示例域名不当作真实官网。

2. 先验证地址与访问状态。用户要求打开页面时使用可用浏览器入口；只要求列表时保持只读检索。

3. 仓库模式通过已确认 repo 的 cases 目录读取名称与说明，处理分页和路径编码，保留真实 URL。

4. 空目录、404、权限不足和解析失败分别说明；不可访问时不能伪报没有案例。

5. 结果说明测试名称、简介和可用入口；不创建测试、不提交案例，也不将人格测试结果作临床判断。

## Composition

执行前读取 [能力组合](references/skill-composition.md)，按明确制品交接相邻能力。

## Runtime context (shared)

运行前读取本包 `skill.yaml` 与 [Profile 合同](references/user-profile.md)。优先级为当前请求、
项目上下文、本 Skill records、共享 preferences、brand/user Profile、安全默认值。
只读取声明字段；没有专用运行时的宿主可使用 `scripts/profile_store.py` 读取共享 Profile。
配置缺失只问影响结果的一个问题。用户明确要求长期保存的值通过该脚本原子写入，
报告实际路径；不保存推断、凭据或其他任务的资料。
