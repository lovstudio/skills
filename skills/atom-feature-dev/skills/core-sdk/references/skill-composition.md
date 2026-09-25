# Skill Group Composition

## Nearby Skills Inspected

Feature Contract 是上游；CLI、API、UI 与 Agent adapters 是下游。现有项目库与服务实现是优先复用对象。

## Atomic Handoffs

接收 contract 与 acceptance vectors，输出目标语言 SDK、公开类型和测试证据；本模块拥有业务规则唯一性。

## Overlap Decisions

不复制 adapter、传输或 UI 逻辑；已有可调用核心时扩展而非新建平行 SDK。

## Composition Decision

Atom Core SDK 是 lov-atom-feature-dev 自包含 Kit 的内嵌模块。它拥有独立输入输出与验收，
但只通过根 manifest 与同 Kit 模块硬耦合；外部 Skills 都是可选的制品级交接。

