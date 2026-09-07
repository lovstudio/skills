---
name: lov-kill-emoji
depends_on:
- lov-branding-consistency
description: 将界面中不合适的 emoji 替换为语义一致的图标或简洁文案。支持明确输入与结果回读。Use to replace interface emoji
  with appropriate icons.
license: MIT
compatibility: 支持 Agent Skills 的宿主；Python 3.8+ 与 PyYAML 用于 Profile 和校验。业务工具要求见工作流。
metadata:
  author: contributors
  version: 1.0.1
  content_class: microcopy
  card_standard: lovstudio/skill-card/v1
  tags:
  - kill-emoji
  - portable-skill
---

# Emoji 换装 · Emoji Makeover

将界面中不合适的 emoji 替换为语义一致的图标或简洁文案。

## Triggers

### Activate when

- The user asks to use this Skill for its documented outcome.

- “将界面中不合适的 emoji 替换为语义一致的图标或简洁文案。”
- “Replace interface emoji with appropriate icons.”

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

1. 扫描用户可见 JSX、组件、按钮、提示和菜单，记录位置与用途；源数据、用户输入、引文、代码与有语义的符号保持原样。

2. 区分装饰、交互图标和内容，先判断是否需要图形；不把所有箭头、勾选或 Unicode 字符都视为 emoji。

3. 优先使用项目已有图标库和语义映射，React 可复用 lucide 或 Radix，不为此另装重复库。

4. 修改 import、尺寸、颜色和布局，设置装饰图 aria-hidden，为仅图标按钮保留可访问名称。

5. 运行类型检查并回看受影响组件，报告替换与保留理由，不影响服务端数据或日志。

## Composition

执行前读取 [能力组合](references/skill-composition.md)，按明确制品交接相邻能力。

## Runtime context (shared)

运行前读取本包 `skill.yaml` 与 [Profile 合同](references/user-profile.md)。优先级为当前请求、
项目上下文、本 Skill records、共享 preferences、brand/user Profile、安全默认值。
只读取声明字段；没有专用运行时的宿主可使用 `scripts/profile_store.py` 读取共享 Profile。
配置缺失只问影响结果的一个问题。用户明确要求长期保存的值通过该脚本原子写入，
报告实际路径；不保存推断、凭据或其他任务的资料。
