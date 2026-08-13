# Skill Group Composition

## Nearby Skills Inspected

| Skill or module | Classification | Decision |
| --- | --- | --- |
| `lov-china-website-filing` | owning Kit | 提供共享 Profile、权威规则、提交门、状态词表和统一台账。 |
| `lov-fact-check` | optional external atom | 只接受明确的制品级交接，不作为隐藏依赖。 |
| Kit sibling modules | upstream/downstream atoms | 通过域名、阶段状态、证据时间和下一动作交接。 |

## Atomic Handoffs

- 上游：domain-cutover 的真实网站、开通时间、ICP 号、接入商和服务器证据
- 本模块：公安联网备案。
- 下游：将申请时间、状态、审核单位、公安号或补充要求交给 filing-monitor

## Overlap Decisions

不把一般网络安全加固、等保测评或通用法律咨询并入公安联网备案。

## Composition Decision

本模块是 `lov-china-website-filing` 的**内嵌原子模块**。它可单独调用，但跨阶段时依赖 Kit 内共享的证据和完成门；不拆成外部安装依赖。

