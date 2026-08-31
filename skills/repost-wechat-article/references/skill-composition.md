# Skill Group Composition

## Nearby Skills Inspected

- `lov-wdb-cli`：只读检索本地微信聊天、联系人和分享消息，输出带数据库、表、rowid 的稳定记录；不处理公开文章正文或公众号草稿。
- `lov-publish-wechat-article`：消费完成的 Markdown、Lovpen 微信 HTML、封面收据和账号 locator，拥有图片上传、草稿创建、远端回读与正式发布状态；不负责定位合作方原文或划分转载冻结区。
- `lov-wechat-article-branding-skill`：对整篇公众号文章做结构、视觉和品牌化；可能改写内容结构，因此只有在冻结原文边界明确后才作为可选品牌上游。
- `lov-wechat-article-operator`：读取或最小修改既有公众号草稿，并保存重载验证；不创建新的转载版本。
- `lov-branding-consistency`：审校新增开场、收尾和品牌微文案；不得改写来源正文、名称、数字、引语或链接。

## Atomic Handoffs

| Role | Owner | Input | Output | Acceptance owner |
| --- | --- | --- | --- | --- |
| Upstream atom | `lov-wdb-cli`（可选） | 合作方、日期、标题或聊天语境 | 带稳定 source 的文章分享 URL 与内部上下文 | WDB 负责记录命中；本 Skill 决定哪些语境可公开 |
| Core atom | `lov-repost-wechat-article` | 公开原文、允许公开的合作语境、品牌 Profile | 冻结原文、发布方增量、来源账本与转载 manifest | 本 Skill 负责来源忠实、权利模式和私密隔离 |
| Downstream atom | `lov-publish-wechat-article` | canonical Markdown、Lovpen HTML、封面与收据 | `draft_created` 或经明确授权后的 `published` 收据 | 发布 Skill 负责平台状态；本 Skill 复核远端冻结区 |
| Downstream atom | `lov-wechat-article-operator`（可选） | 精确 `mediaId` 和允许修改字段 | 保存并重载后的既有草稿 | Operator 负责最小修改与持久化 |

## Overlap Decisions

- 不扩展普通发布 Skill：它的输入是已经完成的文章，不能替代来源定位、转载权利判断、原文冻结和发布方增量审计。
- 不扩展全篇品牌化 Skill：转载的关键门禁是原文主体不可被品牌化过程改写，应由独立核心 Skill 先建立冻结边界。
- 不复制 WDB、Lovpen、封面合成、图片上传或微信网关代码；交接只通过 URL、文件、manifest 和收据发生。

## Composition Decision

选择 Single Skill。来源定位、冻结、增量编辑和转载审计共同服务于一个用户结果，单独拆成可触发模块价值有限；真正独立的 WDB、品牌化、Operator 与发布能力已经存在，保持外部原子并通过明确产物交接更简单。`lov-publish-wechat-article` 是显式下游依赖，不是隐藏实现。

