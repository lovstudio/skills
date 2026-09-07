---
name: lov-output
depends_on:
- lov-branding-consistency
description: 将已确认内容按指定文件名与文本格式保存并回读校验。支持明确输入与结果回读。Use to save the current content
  to a file.
license: MIT
compatibility: 支持 Agent Skills 的宿主；Python 3.8+ 与 PyYAML 用于 Profile 和校验。业务工具要求见工作流。
metadata:
  author: contributors
  version: 0.1.1
  content_class: verbatim
  card_standard: lovstudio/skill-card/v1
  tags:
  - output
  - portable-skill
---

# 内容收纳 · Content Keeper

将已确认内容按指定文件名与文本格式保存并回读校验。

## Triggers

### Activate when

- “将已确认内容按指定文件名与文本格式保存并回读校验。”
- “Save the current content to a file.”

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

1. 从请求确定要保存的文本、路径和格式；无法识别具体内容才问一个聚焦问题，不把会话全部内容默认为公开制品。

2. 无扩展名默认 .md，路径优先用户指定；无路径时在当前项目 output 内生成不冲突名称。保留中文编码，不覆盖已有同名文件。

3. Markdown 使用正确围栏和内联代码；JSON、YAML、CSV 使用对应序列化器并校验，CSV 正确引用换行、逗号与公式敏感内容。

4. 保持源文本事实与原意；用户仅要求保存时不润色、添加总结或删改引文。PDF、Word 等二进制格式使用可用专用工具，不能改扩展名伪装。

5. 写后回读内容、编码与大小，交付真实文件链接；不自动上传、发布或打开前台应用。

## Composition

执行前读取 [能力组合](references/skill-composition.md)，按明确制品交接相邻能力。

## Runtime context (shared)

运行前读取本包 `skill.yaml` 与 [Profile 合同](references/user-profile.md)。优先级为当前请求、
项目上下文、本 Skill records、共享 preferences、brand/user Profile、安全默认值。
只读取声明字段；没有专用运行时的宿主可使用 `scripts/profile_store.py` 读取共享 Profile。
配置缺失只问影响结果的一个问题。用户明确要求长期保存的值通过该脚本原子写入，
报告实际路径；不保存推断、凭据或其他任务的资料。
