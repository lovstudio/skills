---
name: lov-legal-pages
depends_on:
- lov-branding-consistency
description: 根据真实业务与数据处理事实生成隐私政策和服务条款页面草稿。支持明确输入与结果回读。Use to draft website privacy
  and terms pages.
license: MIT
compatibility: 支持 Agent Skills 的宿主；Python 3.8+ 与 PyYAML 用于 Profile 和校验。业务工具要求见工作流。
metadata:
  author: contributors
  version: 1.1.1
  content_class: authored-prose
  card_standard: lovstudio/skill-card/v1
  tags:
  - legal-pages
  - portable-skill
---

# 网站条款助手 · Website Legal Pages

根据真实业务与数据处理事实生成隐私政策和服务条款页面草稿。

## Triggers

### Activate when

- The user asks to use this Skill for its documented outcome.

- “根据真实业务与数据处理事实生成隐私政策和服务条款页面草稿。”
- “Draft website privacy and terms pages.”

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

1. 读取网站业务、数据收集、用途、存储、第三方处理者、支付、退款、联系主体与适用地区。缺少实质事实时提出聚焦问题，不臆造公司地址、保留期限或合规承诺。

2. 检查当前适用的官方法律与平台材料，用实际事实组织隐私政策和服务条款；明确文本为待负责人员审阅的草稿，不能宣称法律合规认证。

3. 复用网站布局、语言、日期与链接约定，创建用户指定页面与路由；已有法律原文保持来源忠实，改动清晰可审。

4. 只有请求范围包含导航接入时修改 Footer；不自动上线页面或同意任何协议。

5. 检查渲染、链接、联系信息、日期和事实一致性，列出需要主体确认的缺口并保持草稿状态。

## Composition

执行前读取 [能力组合](references/skill-composition.md)，按明确制品交接相邻能力。

## Runtime context (shared)

运行前读取本包 `skill.yaml` 与 [Profile 合同](references/user-profile.md)。优先级为当前请求、
项目上下文、本 Skill records、共享 preferences、brand/user Profile、安全默认值。
只读取声明字段；没有专用运行时的宿主可使用 `scripts/profile_store.py` 读取共享 Profile。
配置缺失只问影响结果的一个问题。用户明确要求长期保存的值通过该脚本原子写入，
报告实际路径；不保存推断、凭据或其他任务的资料。

作者性文本执行 [作者性与来源合同](references/authorship-integrity.md)，不编造作者经历、事实或来源。
