# Skill Group Composition

## Nearby Skills Inspected

Core SDK 与 Feature Contract 是上游；Profile Experience、Dashboard 和生产发布是下游。lov-cli-creator 可实现完整 CLI，lov-skill-creator 可打包独立 Skill。

## Atomic Handoffs

接收 SDK、schema 与测试向量，输出 CLI、REST API、Agent Skill 中适用的 adapters；本模块拥有跨 surface 等价性。

## Overlap Decisions

不复刻 SDK 业务规则，也不把渠道发布状态归为本模块完成。

## Composition Decision

Atom Distribution Surfaces 是 lov-atom-feature-dev 自包含 Kit 的内嵌模块。它拥有独立输入输出与验收，
但只通过根 manifest 与同 Kit 模块硬耦合；外部 Skills 都是可选的制品级交接。

