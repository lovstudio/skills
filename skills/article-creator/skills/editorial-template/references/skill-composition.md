# Skill composition

## Nearby Skills Inspected

`lov-wechat-article-operator` 可编辑后台旧稿；`lov-publish-wechat-article` 可创建草稿或发布。

## Atomic Handoffs

本模块接收 Markdown 与元数据，输出标准文章包给 `lov-cover-package` 和 `lov-quality-gate`。

## Overlap Decisions

模板装配保留在 Kit 内；公众号后台写入保持外部可选，因为它会改变远端状态。

## Composition Decision

本模块只产生本地 `pending_validation` 包，不把远端 Operator 或 Publisher 作为隐藏依赖。
