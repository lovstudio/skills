# Skill 组合边界

本 Skill 是微信公众号所有远端状态变化的唯一公开入口。它消费已经完成的文章与视觉资产，并对已有草稿读取、最小修改、草稿创建、保存重载、远端回读和正式发布状态负责。

## Public architecture

| Skill | Owner |
| --- | --- |
| `lov-writing-style` | 通用文风；内部调用 `lov-human-writing` |
| `lov-human-writing` | 唯一反 AI / 作者性审计规则源 |
| `lov-article-creator` | 公众号离线创作、品牌化、转载与 `prepared` 文章包 |
| `lov-publish-wechat-article` | 公众号远端读取、编辑、草稿、核验与发布 |

`lov-wechat-article-operator` 已迁入本 Skill 的 `existing-draft` 流程，不再作为独立运行时依赖。`lov-wechat-article-branding-skill` 与 `lov-repost-wechat-article` 已由 `lov-article-creator` 收拢。

## Nearby atoms

| 相邻能力 | 交接物 | 验收归属 |
| --- | --- | --- |
| `lovpen-cli` | `--format wechat` 复制态 HTML | Lovpen 负责本地渲染；本 Skill 负责上传与远端版式回读 |
| `lov-wechat-branding-cover-composition` | 分享封面与合成收据 | 上游负责视觉证据；本 Skill 验收、上传并回读 |
| `lov-image-decorator` | Caption 派生图片与收据 | 上游负责单图合成；本 Skill 决定文章语境并核对发布结果 |
| 公众号品牌 Profile | endcap、个人卡片、活动状态 | 上游写入 Markdown；本 Skill 在远端写入前失败关闭 |
| `lov-article-creator` | `prepared` 包、转载 manifest 与保真记录 | Creator 负责内容和本地制品；本 Skill 负责远端持久化 |
| `lov-env-management` | AppSecret 与网关 Key locator | Env 负责秘密解析；本 Skill 不持久化秘密 |

## Atomic handoffs

- 新草稿接收 canonical Markdown、独立 `4:3` 正文首图、分享封面收据与 Lovpen 微信复制态 HTML。
- 已有草稿先生成 before snapshot 与 mutation plan，再执行最小修改；after snapshot 必须通过 `verify_article_state.py`。
- 转载草稿额外核对冻结来源正文散列、图片账本与 `copyrightMode: reprint`。
- 输出只使用可观察状态：`draft_read`、`draft_saved`、`draft_created`、`draft_ready`、`published` 等；本地成功或接口 `ret=0` 不替代远端回读。

## Composition decision

保持 Single Skill。已有草稿编辑、创建新草稿、补齐编辑器字段与正式发布共享同一账号、授权门、状态机和收据；拆成多个公开 Skill 会重新制造路由歧义和状态误报。
