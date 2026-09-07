---
name: lov-i18n-check-i18n
description: 检查并修复用户可见文案硬编码、缺失翻译键及语言配置。支持明确输入与结果回读。Use to review and fix frontend
  internationalization.
license: MIT
compatibility: 支持 Agent Skills 的宿主；Python 3.8+ 与 PyYAML 用于 Profile 和校验。业务工具要求见工作流。
depends_on:
- lov-branding-consistency
metadata:
  author: contributors
  version: 1.0.1
  content_class: microcopy
  card_standard: lovstudio/skill-card/v1
  tags:
  - i18n-check-i18n
  - portable-skill
---

# 国际化巡检 · I18n Inspector

检查并修复用户可见文案硬编码、缺失翻译键及语言配置。

## Triggers

### Activate when

- “检查并修复用户可见文案硬编码、缺失翻译键及语言配置。”
- “Review and fix frontend internationalization.”

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

1. 读取框架、现有 i18n 库、语言目录与默认 locale。已有方案继续使用，不仅因为缺翻译就换库；确需初始化时从产品受众确定语言。

2. 扫描可见 JSX、placeholder、title、错误和通知文本，排除日志、代码标识符、路径、数据、引文和产品专名。

3. 按组件语义生成稳定 key，维护现有命名空间；各语言保持占位变量、复数规则和 ICU 语法一致，避免字符串拼接破坏语序。

4. 更新调用与语言文件，保留已有人工翻译；报告尚缺依据的译文，不把机器初稿标作专业审校。

5. 运行类型与翻译完整性检查，验证语言切换、fallback、日期数字和布局。提交仅在请求包括提交时执行。

## Composition

执行前读取 [能力组合](references/skill-composition.md)，按明确制品交接相邻能力。

## Runtime context (shared)

运行前读取本包 `skill.yaml` 与 [Profile 合同](references/user-profile.md)。优先级为当前请求、
项目上下文、本 Skill records、共享 preferences、brand/user Profile、安全默认值。
只读取声明字段；没有专用运行时的宿主可使用 `scripts/profile_store.py` 读取共享 Profile。
配置缺失只问影响结果的一个问题。用户明确要求长期保存的值通过该脚本原子写入，
报告实际路径；不保存推断、凭据或其他任务的资料。
