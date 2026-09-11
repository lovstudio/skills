# Skill Group Composition

## Nearby Skills Inspected

| Skill | Classification | Decision |
| --- | --- | --- |
| `lov-read-codex-session` | upstream atom | 读取指定 thread 的回合、状态与工具活动；本 Skill 需要它的实时状态作为取证补充，但它不负责 400 的成因与处置。 |
| `lov-fix-general` | overlap, 保持分离 | 通用报错排错；本 Skill 只处理 DeepSeek responses 通道上的这一类 400 与 thread 锁死，触发条件更窄。 |
| `lov-fix-by-add-log` | not composed | 面向可复现缺陷的日志插入；本事故的成因来自宿主批次与提示插入，加日志不是主路径。 |
| `lov-fix-until-no-error` | not composed | 面向有明确验证命令的迭代修复；本事故的"修复"是规避与恢复，不是让同一条命令变绿。 |
| `lov-describe-image` | downstream atom | 提供外部视觉通道，让会话内不再调用 view_image；本 Skill 在预防清单里把它列为推荐的替代路径。 |
| `lov-feedback-loop` | downstream atom | 把反复出现的 400 记成可统计的反馈事件并闭环；本 Skill 产出的事实可交给它记账。 |
| `lov-mobile-infographic` | not composed | 事故的工作负载之一（系列卡复核），不是本 Skill 的前置能力。 |

## Atomic Handoffs

```text
lov-fix-deepseek-tool-call-error
  事故清单 + 恢复方案 + 预防清单
        |
        +--> optional: lov-read-codex-session（读 thread 实时状态）
        +--> optional: lov-describe-image（会话外看图通道）
        +--> optional: lov-feedback-loop（把复发记成反馈事件）
```

- 上游交接：无硬依赖。会话目录读取与扫描器自包含在 `scripts/` 内。
- 下游交接：恢复方案交回用户或当前 thread 执行；外部看图交 `lov-describe-image`；
  复发统计交 `lov-feedback-loop`。三者都是可选，不构成本 Skill 的运行前提。
- 验收边界：本 Skill 拥有"事故判定与预防规则"，不拥有 Codex 本体的修复，也不拥有
  远程发布。

## Overlap Decisions

- 与通用排错 Skill 的重叠通过触发条件区分：只有 DeepSeek responses 通道上的
  `No tool output found for tool call` 才进入本 Skill；其它报错交给 `lov-fix-general`。
- 与 `lov-read-codex-session` 的分工是"读状态"与"断因果"：前者回答做到哪了，后者回答
  为什么死、怎么不再死。
- 不复用 `lov-fix-by-add-log` 或 `lov-fix-until-no-error`，因为本事故没有可加日志的本地
  代码路径，也没有一条能变绿的验证命令；验证方式是"不再新增事故 + 规则回读"。

## Composition Decision

`lov-fix-deepseek-tool-call-error` 是 **Single Skill**：一个扫描器加三份 reference 就能
覆盖取证、恢复与预防，没有可独立触发的第二阶段，也不需要在运行时依赖任何 sibling
Skill。外部能力保持为可选的 artifact 级交接。

