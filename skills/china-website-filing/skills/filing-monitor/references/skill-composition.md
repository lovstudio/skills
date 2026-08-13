# Skill Group Composition

## Nearby Skills Inspected

| Skill or module | Classification | Decision |
| --- | --- | --- |
| `lov-china-website-filing` | owning Kit | 提供共享 Profile、权威规则、提交门、状态词表和统一台账。 |
| `automation-workflows` | optional external atom | 只接受明确的制品级交接，不作为隐藏依赖。 |
| Kit sibling modules | upstream/downstream atoms | 通过域名、阶段状态、证据时间和下一动作交接。 |

## Atomic Handoffs

- 上游：任一备案模块提供的权威入口、上一状态、完成门与通知策略
- 本模块：备案状态巡检。
- 下游：宿主调度/通知系统只消费 changed、needs_user_action 和完成信号

## Overlap Decisions

内嵌状态比较和备案语义；通用自动化只负责触发与投递，不重新解释状态。

## Composition Decision

本模块是 `lov-china-website-filing` 的**内嵌原子模块**。它可单独调用，但跨阶段时依赖 Kit 内共享的证据和完成门；不拆成外部安装依赖。

