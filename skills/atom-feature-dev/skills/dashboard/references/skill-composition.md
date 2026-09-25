# Skill Group Composition

## Nearby Skills Inspected

Manifest、Profile resolver、surface adapters 和 Operations evidence 是上游；真实用户调试与发布决策是下游。

## Atomic Handoffs

接收真实控制面数据，输出 atom index、Run、Compare、Evidence、Operations 和 Logs；本模块拥有状态可追溯性与跨 surface 调试体验。

## Overlap Decisions

不替代通用监控后台，不用手填状态冒充验证，也不在浏览器暴露秘密。

## Composition Decision

Atom Feature Dashboard 是 lov-atom-feature-dev 自包含 Kit 的内嵌模块。它拥有独立输入输出与验收，
但只通过根 manifest 与同 Kit 模块硬耦合；外部 Skills 都是可选的制品级交接。

