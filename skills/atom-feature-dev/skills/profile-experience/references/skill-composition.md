# Skill Group Composition

## Nearby Skills Inspected

Feature Contract 提供参数与 Preset schema；Distribution Surfaces 和 Dashboard 消费 resolved parameters。lov-integrate-agent-uiux 只负责通用对话组件。

## Atomic Handoffs

接收共享 schema、Profile 存储和目标 UI，输出 Preset 编辑器、解析器和减少追问的 Agent 参数；本模块拥有参数来源与覆盖体验。

## Overlap Decisions

不创建整套 App shell，不复制业务默认值，不把临时输入或秘密持久化。

## Composition Decision

Atom Profile Experience 是 lov-atom-feature-dev 自包含 Kit 的内嵌模块。它拥有独立输入输出与验收，
但只通过根 manifest 与同 Kit 模块硬耦合；外部 Skills 都是可选的制品级交接。

