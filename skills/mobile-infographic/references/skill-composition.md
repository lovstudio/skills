# Skill Group Composition

本记录说明 adjacent Skill 的边界、交接产物与最终形态选择，避免与已有能力重复或形成隐藏依赖。

## Nearby Skills Inspected

| Skill | 真实路由契约 | 与本 Skill 的关系 |
| --- | --- | --- |
| `lov-professional-infographic` | 证据驱动的咨询 Exhibit，默认 16:9 主版，输出 poster.html 与 3200×1800 PNG，附 brief.md、source.md、audit.json | 最接近的同类。本 Skill 是面向手机单列阅读的重排能力：画布 1080 宽、默认 long 自适应高度、字号下限、行宽上限与系列页码都是它没有的约束 |
| `lov-gen-card` | 把结构化 JSON 与独立示意图排成固定比例编辑式知识卡，900×1350 预设，强调可复制 Prompt 与图鉴系列 | 输出形态相近，内容模型不同：图鉴卡的核心是示意图与评分字段，本 Skill 的核心是结论与证据，且不做生图 |
| `baoyu-xhs-images` | 生成 1–10 张卡通风格社交媒体图卡，12 风格 8 版式 3 配色，面向种草与互动 | 方向不同：该 Skill 以生图与风格化为目标，本 Skill 以代码排版与可核查口径为目标 |
| `lov-product-onepage` | 产品 Brief 到品牌一页纸宣发海报，含转化文案与产品证据 | 目的不同：宣发海报服务转化叙事，本 Skill 服务结论与证据的移动端复述 |
| `lov-table2image` | Markdown 表格渲染为可访问的 PNG | 可作为上游素材来源；表格本身不进入卡片，卡片只承载从表格提炼出的结论与单个数字 |
| `lov-branding-consistency` | 面向读者可见文本的品牌门禁 | 顶层依赖。本 Skill 的 content_class 为 microcopy，卡片文案的受众、品牌角色与可见性由该规范约束 |
| `lov-media-publisher` | 本地成片到视频号、B 站等渠道的发布与线上回读 | 下游消费者：它能消费本 Skill 产出的 PNG，但两者不共享运行时 |
| `lov-article-creator` / `lov-publish-wechat-article` | 公众号文章包与草稿发布 | 下游消费者：卡片可作为文章内的正文图或分享首图素材 |

## Atomic Handoffs

| 分类 | 归属 | 输入产物 | 输出产物 | 验收边界 |
| --- | --- | --- | --- | --- |
| core atom | 本 Skill | 一段已有结论的内容加上可核查来源 | 默认一张 long 卡：card.html、2× PNG、brief.md、source.md、audit.json；仅显式多张时另附 manifest.json | 机器审计通过且完成原图与缩略图复核 |
| optional upstream | 用户或 `lov-table2image` | 表格、报表、调研材料 | 可提炼的数字与判据 | 单位、周期、分母明确 |
| optional downstream | `lov-article-creator` / `lov-publish-wechat-article` | 通过审计的 PNG | 文章内嵌图或分享首图 | 由下游渠道的可见性回读负责 |
| optional downstream | `lov-media-publisher` | 通过审计的 PNG | 平台发布结果 | 由平台回读负责 |

其他情况不构成交接：本 Skill 不读取其它 Skill 的私有文件，也不调用它们的脚本。

## Overlap Decisions

- 与 `lov-professional-infographic` 刻意分离而不合并：合并会把 16:9 桌面读图与 1080 竖屏读图塞进同一套版式常量与同一份审计阈值，两者对字号、行宽、安全区的要求相反。共享的部分保持在产物层面——同一份证据表可以分别交给两个 Skill。
- 与 `lov-gen-card` 保持各自独立：图鉴卡需要 JSON 预设与示意图槽，本 Skill 需要语义模板与移动可读性门禁，二者共用一套 theme 只会让两边的预设都变复杂。
- 与 `baoyu-xhs-images` 不互相吸收：生图风格化与证据排版的目标函数不同，混用会让文字与数字的所有权变得不清。
- 不新建 `lov-mobile-infographic` 之类的第三个同类 Skill；本 Skill 已经覆盖“手机阅读信息卡”这一结果。

## Composition Decision

判定为 **Single Skill**。定位、选模板、出证据表、排版、渲染与审计属于同一个用户可见结果的不同阶段，
共享同一份品牌配置与同一套阈值常量，拆成 Kit 只会增加调用成本。相邻 Skill 全部按产物交接，
本源码内不引用任何外部 sibling Skill 的模块，运行时只有可选的 Playwright 依赖。
