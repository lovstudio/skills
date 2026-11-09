# Skill Group Composition

## Nearby Skills Inspected

| Skill | Classification | Decision |
| --- | --- | --- |
| `ego-browser` 或其他登录态浏览器能力 | optional upstream atom | 需要登录的平台（如小红书）读取作品列表、作品 ID 与直链；只交接链接与公开元数据，不管理登录。 |
| `lov-media-crawler` | optional upstream atom | 授权链接到可解码的本地媒体与下载报告；样本登记读取它的报告与文件。 |
| `lov-voice2srt` | optional upstream atom | 需要云端 ASR 或热词时产出 SRT/JSON 转写；本 Skill 用 `measure.py import` 规范化后使用。 |
| `lov-xiaonuan-style-media-creator`、`lov-laozhang-style-media-creator` | downstream products (not overlap) | 它们是本流程的产物：各自拥有“按某一种风格出片”的结果。本 Skill 拥有“从任一博主得到风格包”的结果；用户只想按已有风格出片时直接用它们。 |
| `lov-style-clone` | not composed | 只处理文章文风，覆盖不到时间线、版式与声音。 |
| `lov-visual-clone` | not composed | 从单张图提取视觉要素，不处理时间、声音与样本统计。 |
| `lov-media-preprocessor` | optional upstream atom（演示素材） | 用户自己的长录像先做增强与分段，再选演示片段。 |
| `lov-media-creator` | optional downstream atom | 已有素材的完整剪辑、精修与混音；可读取本 Skill 的风格包与模板参数。 |
| `lov-skill-creator` | downstream atom | 用户要求封装时，接收冻结风格包、模板与案例，生成 `lov-SLUG-style-media-creator`。 |
| `lov-skill-publisher` | downstream atom | 只在用户要求时发布封装好的专属 Skill。 |
| `lov-branding-consistency` | declared dependency | 说明书与模板里的读者可见文本过品牌与受众门禁；不改写引文和数字。 |

## Atomic Handoffs

- 上游列表：创作者主页 → 登录态浏览器 → 候选作品 ID、元数据、直链；验收为 ID 去重、属于当前格式期。
- 上游下载：直链或分享链接 → `lov-media-crawler` → 原片与下载报告；验收为 verified、可解码、带音轨。
- 上游转写（可选）：原片 → 外部 ASR → Whisper/听悟/SRT 文件；由 `measure.py import` 规范化，原文不改。
- 核心：样本清单与原片 → 本 Skill → 冻结风格包、留出报告、说明书、模板参数与预览；验收为 `verify` 通过、`FROZEN.json` 与文件一致、留出覆盖完整。
- 下游封装：冻结风格包 + 模板 + 案例 → `lov-skill-creator` → 专属风格 Skill；验收由 Skill 工坊的校验与安装负责。
- 下游精修与发布：演示计划与成片 → 媒体制作或发布能力；本 Skill 不自动发布。

## Overlap Decisions

两个已有的风格 Skill 方法相同（同构的画像、证据与冻结纪律），但它们锁定在各自的风格包上。把“分析任意博主”塞进其中任何一个，都会让一个风格包里混入另一种风格的切换逻辑，所以新建通用能力，专属 Skill 保持独立。

本 Skill 的工具在晓暖的真实研究数据上复现了它的 v0.1 冻结包（画像与证据逐字节一致），模板在填入晓暖参数后与她的专用模板逐像素一致。因此，专属 Skill 以后可以改用本 Skill 的工具重做分析，不需要各自维护一套分析脚本。这一迁移不在本版范围内。

## Composition Decision

Single Skill。取样、冻结、测量、规则、留出、说明书与模板参数是同一个结果（一份可信的风格包）的连续阶段：它们共用工作区、样本清单与 Schema，单独拿出任何一段都不能交付可用的结果。两个 CLI（`cloner.py` 台账、`measure.py` 测量）、OCR 程序、音轨构建与模板是实现支撑，不构成可独立售卖的模块。登录、下载、精剪、封装与发布都是可选的文件交接。没有启动子 Agent，也不调用外部模型 API。
