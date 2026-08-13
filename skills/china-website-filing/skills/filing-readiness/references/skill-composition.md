# Skill Group Composition

## Nearby Skills Inspected

| Skill or module | Classification | Decision |
| --- | --- | --- |
| `lov-china-website-filing` | owning Kit | 提供共享 Profile、权威规则、提交门、状态词表和统一台账。 |
| `lov-fill-web-form` | optional external atom | 只接受明确的制品级交接，不作为隐藏依赖。 |
| Kit sibling modules | upstream/downstream atoms | 通过域名、阶段状态、证据时间和下一动作交接。 |

## Atomic Handoffs

- 上游：用户当前请求、品牌 Profile 或可选的 lov-fact-check 规则摘要
- 本模块：备案准备核验。
- 下游：将备案类型、材料清单、实名状态和阻塞项交给 icp-filing

## Overlap Decisions

不复制 lov-fill-web-form 的通用表单知识库检索，也不生成隐私政策或生产制品。

## Composition Decision

本模块是 `lov-china-website-filing` 的**内嵌原子模块**。它可单独调用，但跨阶段时依赖 Kit 内共享的证据和完成门；不拆成外部安装依赖。

