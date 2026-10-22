# 励志片型的能力边界

## Nearby Skills Inspected

2026-10-22按真实入口与输入输出检查了本地来源和共享安装位；没有原有励志片型owner。

| Skill | 分类 | 实际合同 |
|---|---|---|
| lov-writing-style | upstream atom | 核实事实与作者判断 → 个人声音口播；可选 |
| lov-branding-consistency | upstream atom | Profile与可见稿 → 在位品牌审校；声明必需语义依赖 |
| lov-motivational-media-creator | core atom | 真实处境与行动 → 励志片型原创制作包 |
| lov-media-creator | downstream atom | 剧本、素材、cue → Studio审片、渲染与媒体QC |
| general-video | downstream atom | brief、分镜与素材 → 通用视频composition；可选替代后端 |
| lov-media-publisher | downstream atom | 批准成片、字幕封面 → 获授权渠道发布及回读 |
| lov-logo-sting | downstream atom，可选 | 官方Logo SVG、fps、节拍网格 → 片尾Logo动画与音效（Remotion Sequence或sting.mp4） |
| lov-motion-media-creator | not composed | 动态图鉴/地图/工序，不是实拍励志蒙太奇 |
| lov-article-creator | not composed | 公众号文章，不拥有视频结果 |
| lov-media-fetch | not composed | 影视检索下载，不是YouTube频道研究器 |
| lov-media-crawler | upstream atom，范围受限 | 少量社交链接→核验媒体；不声明账号批量或YouTube支持 |

## Atomic Handoffs

- 品牌审校：本Skill给可见文案与品牌brief，审校器回填；本Skill负责制作包最终验收。
- 可选文风器：核实事实/完整口播草稿交接，返回声音适配稿；不得新增经历。
- 媒体执行器：交production JSON、脚本、分镜、素材权利表、字幕和声音cue。
  执行器负责真实成片、横竖版、解码/试听/布局QC；本Skill不能以JSON通过冒充渲染成功。
- 发布器：只在用户另行授权后交批准的渠道素材，发布器负责线上回读。
- 片尾Logo（可选）：仅面向观众的品牌成片，草稿/切片未要求不加；未安装照常收尾。交批准的官方Logo SVG、
  成片fps与配乐节拍网格，取回Sequence或sting.mp4；整条母带响度与真峰值仍由本片成片验收重测
  （参考片AAC编码后需−2.5 dBTP、限幅0.70）。
- 下载研究由本Skill的受限研究协议组织，不假称相邻下载器已覆盖账号批量需求。

## Overlap Decisions

media-creator已将片型风格交给片型owner，本Skill不复制共享渲染、母带、Studio或发布。
现有软件教程、动态图志、文章能力不作励志结果的重复实现；只在明确制品边界可选调用。
共享branding-consistency安装副本和来源版本曾不一致，当前任务不覆盖他人安装，
采用已读canonical规则做语义审校并在外部验收记录说明。

## Composition Decision

Single Skill，instruction-first加一个标准库制作包验收CLI。研究、编剧、分镜共享同一
委托与一次最终验收，非独立产品，无需Kit。可选外部执行器不是隐藏硬依赖。
