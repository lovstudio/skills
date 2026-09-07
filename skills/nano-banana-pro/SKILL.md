---
name: lov-nano-banana-pro
description: 将图像需求整理为结构清晰、遵循参考素材的生成或编辑提示词。支持明确输入与结果回读。Use to create a structured image
  prompt.
license: MIT
compatibility: 支持 Agent Skills 的宿主；Python 3.8+ 与 PyYAML 用于 Profile 和校验。业务工具要求见工作流。
depends_on:
- lov-branding-consistency
metadata:
  author: contributors
  version: 0.1.1
  content_class: microcopy
  card_standard: lovstudio/skill-card/v1
  tags:
  - nano-banana-pro
  - portable-skill
---

# 图像提示词整理

将图像需求整理为结构清晰、遵循参考素材的生成或编辑提示词。

## Triggers

### Activate when

- “将图像需求整理为结构清晰、遵循参考素材的生成或编辑提示词。”
- “Create a structured image prompt.”

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

1. 提取主体、用途、构图、风格、光线、比例、文字要求和参考图约束；真实人物与品牌要求保持忠实。

2. 输出完整主提示词，优先具体可观察的画面指令，不以 8k、masterpiece 等空泛堆词替代内容。

3. 只有目标接口明确支持时提供独立 negative prompt；编辑任务写清需要改变和必须保持的部分。

4. Nano Banana Pro 作为用户指定产品名保留，模型能力从当前官方文档核实，不能凭名字假设动漫或 2.5D 风格。

5. 默认交付提示词；用户另要求生图时使用宿主实际生成能力并验证结果，不能声称仅写提示词已经生成图片。

## Composition

执行前读取 [能力组合](references/skill-composition.md)，按明确制品交接相邻能力。

## Runtime context (shared)

运行前读取本包 `skill.yaml` 与 [Profile 合同](references/user-profile.md)。优先级为当前请求、
项目上下文、本 Skill records、共享 preferences、brand/user Profile、安全默认值。
只读取声明字段；没有专用运行时的宿主可使用 `scripts/profile_store.py` 读取共享 Profile。
配置缺失只问影响结果的一个问题。用户明确要求长期保存的值通过该脚本原子写入，
报告实际路径；不保存推断、凭据或其他任务的资料。
