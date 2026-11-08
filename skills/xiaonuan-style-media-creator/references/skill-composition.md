# Skill Group Composition

## Nearby Skills Inspected

| Skill | Classification | Decision |
| --- | --- | --- |
| `lov-media-crawler` | optional upstream atom | 已授权链接到已验证本地媒体；v0.1 的 12 条输入来自它的直链下载报告。 |
| `ego-browser` | optional upstream atom | 需要登录态的平台（小红书）读取笔记 ID 与直链；只交接链接，不管理登录。 |
| `lov-laozhang-style-media-creator` | not composed (sibling) | 同一套画像/证据/计划协议，但风格与题材不同；两者共享方法，不互相调用。 |
| `lov-style-clone` | not composed | 只处理文章文风，覆盖不到连麦叙事、包装模板与时间线验收。 |
| `lov-visual-clone` | not composed | 只从单张图提取视觉要素，不处理时间线与声音。 |
| `lov-media-creator`、`lov-interview-media-creator` | optional downstream atom | 已有素材的完整剪辑、精修与混音；本 Skill 的剪辑计划与渲染数据可作为输入。 |
| `lov-channels-cover` | optional downstream atom | 需要系列化封面墙时接手；本 Skill 只给单片 3:4 封面。 |
| `lov-media-publisher` | optional downstream atom | 经用户批准的成片发布到视频号、B 站或小红书；本 Skill 不外发。 |

## Atomic Handoffs

- 可选上游下载：授权链接 → 下载能力 → 原视频、报告与哈希；验收为可解码的真实媒体。
- 可选上游转写：原视频 → 带时间戳的 ASR JSON；不得把摘要当原话。
- 核心：参考视频与事实 brief → 本 Skill → 风格协议、证据、剪辑计划、渲染数据与包装成片；验收为来源可核验、计划校验通过、成片质检有记录。
- 可选下游精修：剪辑计划与成片 → 媒体制作能力；由其负责完整观看与混音验收。
- 可选下游发布：经用户批准且有来访者同意的成片 → 发布能力；本 Skill 不自动发布。

## Overlap Decisions

文章文风和单图视觉只是本风格的局部维度，不足以拥有连麦叙事、包装模板与时间线验收，因此不扩展 `lov-style-clone` 或 `lov-visual-clone`。与老张风格 Skill 方法相同但素材、规则与模板都不同，保持两个独立 Skill，避免在一个包里切换作者风格。完整精修与发布交给下游，不复制其流程。

## Composition Decision

Single Skill。画像、创作、校验与包装模板共享同一份风格 JSON、证据与时间线协议；分析脚本与出片脚本是同一结果的实现支撑，不是可独立售卖的阶段。没有启动子 Agent，也没有调用外部模型 API。
