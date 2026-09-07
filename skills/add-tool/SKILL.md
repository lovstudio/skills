---
name: lov-add-tool
description: 为现有网站新增可用的在线工具，并接入多语言、工具目录、站点地图和必要的成本提示。支持明确输入与结果回读。Use to add an online
  tool to an existing website.
license: MIT
compatibility: 支持 Agent Skills 的宿主；Python 3.8+ 与 PyYAML 用于 Profile 和校验。业务工具要求见工作流。
depends_on:
- lov-branding-consistency
metadata:
  author: contributors
  version: 0.1.0
  content_class: deterministic-output
  card_standard: lovstudio/skill-card/v1
  tags:
  - add-tool
  - portable-skill
---

# 在线工具集成

为现有网站新增可用的在线工具，并接入多语言、工具目录、站点地图和必要的成本提示。

## Triggers

### Activate when

- “为现有网站新增可用的在线工具，并接入多语言、工具目录、站点地图和必要的成本提示。”
- “Add an online tool to an existing website.”

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

1. 解析目标项目、工具标识、用途、输入输出和是否使用付费服务。先读取项目规则、路由、现有工具、组件库、多语言目录和 Git 状态；项目技术栈与文件布局以实际代码为准，不强制迁移到 React 或 Next.js。

2. 建立从工具组件到注册数据、详情路由、导航、翻译键和 sitemap 的修改映射。标识采用项目已有命名规则；复用现有表单、反馈、复制、加载和错误组件，保持可访问性及窄屏布局。

3. 实现真实转换或处理逻辑，覆盖空输入、非法输入、成功结果、清空与复制；浏览器能力仅在客户端使用。只有框架要求时才添加 use client。禁止交付未替换的组件名、图标或伪代码。

4. 若使用 AI 或付费 API，从项目当前模型目录和计费逻辑读取价格，区分预估与实际费用、输入与输出计价、单位及当前选定模型。无可靠价格时显示待确认，不把固定字符除以四当精确 token。费用扣除留在受鉴权保护的服务端，幂等处理失败和重试；测试采用沙箱或隔离数据，不发起真实扣款。

5. 在实际语言集合中补齐文案并检查键一致性；更新工具注册及所需路由。核实 sitemap 是否真正动态读取注册数据，不能仅凭旧注释断言自动更新；回读目标工具的公开路径和索引策略。

6. 执行相关类型检查、构建与有意义的转换边界测试；在可用运行环境验证工具页、窄屏、输入结果及复制反馈。报告哪些运行效果实际回读，未测部分不宣称通过。

7. 默认交付代码与验证证据。部署依当前请求范围处理；系统通知、邮件或群发需用户明确授权目标受众和消息内容，使用目标项目已配置的服务并回读状态。旧命令里的服务域名、作者身份与广播地址绝不继承为默认值。

## Composition

执行前读取 [能力组合](references/skill-composition.md)，按明确制品交接相邻能力。

## Runtime context (shared)

运行前读取本包 `skill.yaml` 与 [Profile 合同](references/user-profile.md)。优先级为当前请求、
项目上下文、本 Skill records、共享 preferences、brand/user Profile、安全默认值。
只读取声明字段；没有专用运行时的宿主可使用 `scripts/profile_store.py` 读取共享 Profile。
配置缺失只问影响结果的一个问题。用户明确要求长期保存的值通过该脚本原子写入，
报告实际路径；不保存推断、凭据或其他任务的资料。
