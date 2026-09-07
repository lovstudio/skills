---
name: lov-fix-until-no-error
description: 围绕明确验证命令持续定位和修复失败项直到通过或遇到真实阻塞。支持明确输入与结果回读。Use to fix errors until the
  specified checks pass.
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
  - fix-until-no-error
  - portable-skill
---

# 验证修复 · Verified Fixes

围绕明确验证命令持续定位和修复失败项直到通过或遇到真实阻塞。

## Triggers

### Activate when

- “围绕明确验证命令持续定位和修复失败项直到通过或遇到真实阻塞。”
- “Fix errors until the specified checks pass.”

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

1. 从用户命令或项目 scripts 确定成功标准，先执行并保存首个有效错误；不自行扩大为永远无缺陷的承诺。

2. 按根因修复最高阻塞问题，重跑受影响命令，记录变化与结果。禁止 --no-verify、关闭 lint 规则、删除测试或吞掉异常来制造通过。

3. 出现相同失败而假设两次未命中时检查 cwd、环境、版本、服务实例及配置来源，避免原地循环。

4. 原检查通过后只运行必要回归；外部权限、不可用服务或缺数据造成真实阻塞时如实停在可继续状态，不死循环。

5. 交付通过的具体命令和未覆盖边界。

## Composition

执行前读取 [能力组合](references/skill-composition.md)，按明确制品交接相邻能力。

## Runtime context (shared)

运行前读取本包 `skill.yaml` 与 [Profile 合同](references/user-profile.md)。优先级为当前请求、
项目上下文、本 Skill records、共享 preferences、brand/user Profile、安全默认值。
只读取声明字段；没有专用运行时的宿主可使用 `scripts/profile_store.py` 读取共享 Profile。
配置缺失只问影响结果的一个问题。用户明确要求长期保存的值通过该脚本原子写入，
报告实际路径；不保存推断、凭据或其他任务的资料。
