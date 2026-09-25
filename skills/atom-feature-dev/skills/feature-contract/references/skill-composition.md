# Skill Group Composition

## Nearby Skills Inspected

根 controller 是上游；Core SDK、Distribution Surfaces、Profile Experience 与 Dashboard 是下游。lov-solution-architect 可提供已批准 brief，但不拥有契约。

## Atomic Handoffs

接收用户结果与仓库类型，输出 manifest、contract schema、profile schema 和 acceptance vectors；本模块拥有原子边界与契约验收。

## Overlap Decisions

不替代 API 文档、UI 表单或宽泛架构方案；这些能力只消费已批准契约。

## Composition Decision

Atom Feature Contract 是 lov-atom-feature-dev 自包含 Kit 的内嵌模块。它拥有独立输入输出与验收，
但只通过根 manifest 与同 Kit 模块硬耦合；外部 Skills 都是可选的制品级交接。

