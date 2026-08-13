# Skill Group Composition

## Nearby Skills Inspected

| Skill or module | Classification | Decision |
| --- | --- | --- |
| `lov-china-website-filing` | owning Kit | 提供共享 Profile、权威规则、提交门、状态词表和统一台账。 |
| `lov-fact-check` | optional external atom | 只接受明确的制品级交接，不作为隐藏依赖。 |
| Kit sibling modules | upstream/downstream atoms | 通过域名、阶段状态、证据时间和下一动作交接。 |

## Atomic Handoffs

- 上游：filing-readiness 的备案类型、材料、实名与资源核验结果
- 本模块：ICP 申请与审核。
- 下游：将 ICP 通过证据、服务备案号、域名和接入资源交给 domain-cutover

## Overlap Decisions

通用表单填充只可提供草稿；本模块拥有备案状态机、短信核验和管局完成门。

## Composition Decision

本模块是 `lov-china-website-filing` 的**内嵌原子模块**。它可单独调用，但跨阶段时依赖 Kit 内共享的证据和完成门；不拆成外部安装依赖。

