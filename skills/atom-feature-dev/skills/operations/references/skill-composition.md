# Skill Group Composition

## Nearby Skills Inspected

已实现的 atom 和验证证据是上游；Auth、SEO、定价、dev-to-prod 与发布能力可作为可选下游。

## Atomic Handoffs

接收真实 manifest 与制品，输出 docs、tests、SEO/GEO、Auth、payment、analytics 的适用性矩阵和完成证据；各渠道仍拥有自己的上线状态。

## Overlap Decisions

不强制所有运营项，也不把本地生成或 API 成功写成已上线。

## Composition Decision

Atom Operations 是 lov-atom-feature-dev 自包含 Kit 的内嵌模块。它拥有独立输入输出与验收，
但只通过根 manifest 与同 Kit 模块硬耦合；外部 Skills 都是可选的制品级交接。

