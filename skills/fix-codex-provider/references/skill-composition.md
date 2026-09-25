# Skill Group Composition

## Nearby Skills Inspected

| Skill | Classification | Decision |
| --- | --- | --- |
| `lov-fix-deepseek-tool-call-error` | adjacent atom | 同为 Codex 会话急救，但失败信号是 `No tool output found for tool call` 与 thread 锁死；provider 解析失败必须单独判定，不能互相套用结论。 |
| `lov-open-codex-session` | optional downstream atom | 修复完成后的打开动作；它按 thread UUID 打开任务，不诊断 provider，也不改状态。 |
| `lov-read-codex-session` | optional upstream atom | 只读会话进度与状态；本 Skill 的诊断脚本自带索引与日志取证，不依赖它也能完成判定。 |
| `lov-fix-general` / `debug-pro` | not composed | 面向产品代码缺陷的通用排错；本 Skill 只处理本机 Codex 配置与状态不一致。 |
| `lov-check-balance` | not composed | 话题相邻（provider 账号），目标不同（额度查询），没有工件级交接。 |

## Atomic Handoffs

```text
可选: lov-read-codex-session
  会话状态与进度（只读参考）
            |
            v
lov-fix-codex-provider
  对齐后的 provider 定义/标签 + 诊断与回读报告 + 回滚备份
            |
            v
可选: lov-open-codex-session
  在 Codex 主窗口打开已修复的会话
```

交接发生在工件层：修复报告与备份路径可以交给用户或后续 Skill 使用，不存在隐式的
跨 Skill 运行依赖。

## Overlap Decisions

- 与 `lov-fix-deepseek-tool-call-error` 的分界是失败签名：本 Skill 处理
  `Model provider ... not found`、`invalid_config`、会话打不开；工具调用类 400 交给它。
- 与 `lov-open-codex-session` 的分界是「打开」与「修好再打开」：本 Skill 的验证步骤
  可以调用它，但不复制其实现。
- 不新建通用「Codex 修复」入口：provider 对齐有独立的持久化事实与写操作，独立成 Skill
  才能给出准确的触发条件与安全边界。

## Composition Decision

`lov-fix-codex-provider` 保持 **Single Skill**。诊断、判定、修复计划、写入与回滚是同一
条确定性流水线，共用一个脚本与一份报告；拆成 Kit 只会让备份和确认步骤跨模块漂移。
相邻 Skill 仅作为可选交接，不构成硬依赖。
