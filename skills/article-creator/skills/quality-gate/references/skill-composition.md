# Skill composition

## Nearby Skills Inspected

`lov-wechat-article-operator` 与 `lov-publish-wechat-article` 是验收后的可选远端下游。

## Atomic Handoffs

本模块接收完整文章包，输出 `quality-report.json`；通过后只把本地状态提升为 `prepared`。

## Overlap Decisions

自动规则与人工语义检查都由质量门负责，远端上传与回读仍由发布能力负责。

## Composition Decision

本模块是 Kit 终点，不创建草稿、不发布，也不把本地成功冒充远端成功。
