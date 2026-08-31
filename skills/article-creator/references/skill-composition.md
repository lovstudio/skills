# Skill Group Composition

## Public entrypoints

公众号内容链只保留四个对外入口：

1. `lov-writing-style`：通用新写、改写与个人文风；
2. `lov-human-writing`：唯一反 AI / 作者性审计规则源，由 writing-style 内置调用；
3. `lov-article-creator`：公众号离线创作、品牌化、转载与文章包验收；
4. `lov-publish-wechat-article`：公众号远端草稿创建、读取、编辑、回读与正式发布。

`lov-branding-consistency` 是跨制品品牌事实与资产约束，不是文章入口。

## Nearby Skills Inspected

- `lov-writing-style` 与 `lov-human-writing`：分别拥有个人文风与作者性，不复制进文章 Kit。
- `lov-publish-wechat-article`：拥有全部公众号远端状态，不在 Creator 内实现。
- `lov-branding-consistency`：提供跨制品品牌事实与资产约束，是基础设施而非文章入口。
- 旧 Branding、Repost、Operator 与 Output Skills：仅作为迁移来源和兼容路由保留。

## Ownership

| 阶段 | Owner | 说明 |
| --- | --- | --- |
| personal voice | `lov-writing-style` | 读取文风 Profile，完成新写与改写 |
| authorship integrity | `lov-human-writing` | 唯一反 AI / 作者性规则源，不负责公众号结构 |
| channel structure | `lov-article-creator` | 公众号题材、论文式 benchmark 结构、品牌与本地制品 |
| brand edition | `lov-article-creator` | publication / brand / products、双比例视觉、封面说明 |
| faithful repost | `lov-article-creator` | 来源冻结区、发布方增量、保真审计与转载 manifest |
| remote mutation | `lov-publish-wechat-article` | 已有草稿最小修改、保存重载、远端回读 |
| draft and publish | `lov-publish-wechat-article` | 创建草稿、状态机、授权门和公开发布 |

## Atomic handoffs

| 交接 | 输入 | 输出 | 验收边界 |
| --- | --- | --- | --- |
| creator → writing-style | truth ledger、reader contract、题材、结构约束 | 个人文风正文 | writing-style 调用 human-writing；creator 不复制规则 |
| writing → package | Markdown、来源、发布元数据 | article package | 结构、品牌、图片与本地状态为 `prepared` |
| repost → package | 来源快照、冻结正文、发布方新增区块 | edition manifest、保真收据 | 文字散列、图片账本、区块唯一性成立 |
| package → publisher | `prepared` 包与明确授权 | 远端草稿或公开文章 | 必须保存、重载并远端回读 |

## Retired public entrypoints

- `lov-wechat-article-branding-skill` → `lov-article-creator` 的 `brand` 管线；
- `lov-repost-wechat-article` → `lov-article-creator` 的 `repost` 管线；
- `lov-wechat-article-operator` → `lov-publish-wechat-article` 的 `existing-draft` 管线；
- `lov-output-for-article` → 宿主文件保存或 `lov-article-creator` 文章包输出；
- `lov-anti-wechat-ai-check` → `lov-human-writing`。

这些旧目录只保留兼容路由和历史实现，不参与新任务发现，也不再拥有规则。

## Overlap Decisions

文章题材、品牌版本、转载冻结和本地制品共同服务同一个 `prepared` 文章包，因此归入 Creator。个人文风和作者性仍由专门 Skill 持有；公众号远端操作会改变外部状态，统一留在 Publisher。

## Composition Decision

Creator 保持一个公开入口和一组内部管线。对外路由按“通用写作 / 作者性审计 / 公众号本地制品 / 公众号远端状态”分层，不再按创作、品牌、转载、保存等动作继续拆入口。
