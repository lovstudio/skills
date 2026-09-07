---
name: lov-gen-project-name
description: 根据项目用途提供可用于文件夹与仓库的名称及定位说明。支持明确输入与结果回读。Use to generate a project name
  from its purpose.
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
  - gen-project-name
  - portable-skill
---

# 项目命名

根据项目用途提供可用于文件夹与仓库的名称及定位说明。

## Triggers

### Activate when

- “根据项目用途提供可用于文件夹与仓库的名称及定位说明。”
- “Generate a project name from its purpose.”

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

1. 解析用途、受众、语言与命名限制；需求为空时只问项目做什么。

2. 生成三组不同命名方向，每组给显示名、ASCII slug 与一句解释，避免只堆近义词。

3. slug 使用小写字母、数字与连字符或项目允许的下划线，不以点开头，长度不超过 50 字符；检查目标文件系统保留名及现有目录冲突。

4. 区分产品名、包名和仓库名。未实际查询时不宣称域名、商标或仓库可用；此 Skill 不自动改名或购买域名。

## Composition

执行前读取 [能力组合](references/skill-composition.md)，按明确制品交接相邻能力。

## Runtime context (shared)

运行前读取本包 `skill.yaml` 与 [Profile 合同](references/user-profile.md)。优先级为当前请求、
项目上下文、本 Skill records、共享 preferences、brand/user Profile、安全默认值。
只读取声明字段；没有专用运行时的宿主可使用 `scripts/profile_store.py` 读取共享 Profile。
配置缺失只问影响结果的一个问题。用户明确要求长期保存的值通过该脚本原子写入，
报告实际路径；不保存推断、凭据或其他任务的资料。
