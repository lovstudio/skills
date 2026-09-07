---
name: lov-daily-post
depends_on:
- lov-branding-consistency
description: 将近期真实项目更新写成面向读者的简短日更文案。支持明确输入与结果回读。Use to write a daily project update
  from real changes.
license: MIT
compatibility: 支持 Agent Skills 的宿主；Python 3.8+ 与 PyYAML 用于 Profile 和校验。业务工具要求见工作流。
metadata:
  author: contributors
  version: 1.0.1
  content_class: authored-prose
  card_standard: lovstudio/skill-card/v1
  tags:
  - daily-post
  - portable-skill
---

# 项目日更文案

将近期真实项目更新写成面向读者的简短日更文案。

## Triggers

### Activate when

- “将近期真实项目更新写成面向读者的简短日更文案。”
- “Write a daily project update from real changes.”

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

1. 读取用户指定时段的 CHANGELOG、提交与发布记录，区分已上线能力、开发中内容和计划。

2. 选择读者能理解的一到三个变化，说明具体用途与边界，默认约 300–500 字，长度随素材调整。

3. 采用 Profile 或作者明确指定的身份与语气；技术心得、个人经历、未来计划只有实际资料支持才写。缺素材时省略，不在成稿中留代填提示或虚构第一人称体验。

4. 交付可复制的纯文本，必要链接需核实。没有新进展时如实说明，不编造更新；写稿不自动发公众号。

## Composition

执行前读取 [能力组合](references/skill-composition.md)，按明确制品交接相邻能力。

## Runtime context (shared)

运行前读取本包 `skill.yaml` 与 [Profile 合同](references/user-profile.md)。优先级为当前请求、
项目上下文、本 Skill records、共享 preferences、brand/user Profile、安全默认值。
只读取声明字段；没有专用运行时的宿主可使用 `scripts/profile_store.py` 读取共享 Profile。
配置缺失只问影响结果的一个问题。用户明确要求长期保存的值通过该脚本原子写入，
报告实际路径；不保存推断、凭据或其他任务的资料。

作者性文本执行 [作者性与来源合同](references/authorship-integrity.md)，不编造作者经历、事实或来源。
