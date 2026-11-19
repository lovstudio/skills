# Skill Group Composition

## Nearby Skills Inspected

| Skill | Routing contract | Classification | Decision |
| --- | --- | --- | --- |
| `lov-wxmp-cli` | 读取、检索、导出微探缓存的公众号文章 | upstream atom | 产出 `lov-wxmp-export/v1` 导出目录，本 Skill 只读这个目录，不直接抓微信正文。 |
| `lov-media-crawler` | 下载各平台媒体 | upstream atom | 其他平台的原始素材；文字整理成 Markdown 目录后导入。 |
| `lov-voice2srt` | 音视频转字幕 | upstream atom | 口播平台的转写稿来源。 |
| `lov-media-cloner` | 复刻博主的视频风格（画面、剪辑、包装） | adjacent, not composed | 同一套冻结/留出方法的视频版；画面与剪辑归它，文字与口播稿风格归本 Skill。 |
| `lov-style-clone` | 粘贴样本，即时提取画像并改写一篇 | overlap (lightweight) | 保留为轻量路径；本 Skill 负责账号级语料、逐字证据、留出检验与封装。触发描述互相指向。 |
| `lov-writing-style` | 使用者本人的已校准文风 | not composed | 是“个人文风 Skill”的一个实例，也是本 Skill 封装产物的参照；不混用两个作者。 |
| `lov-skill-creator` | 创建、校验、安装 Skill | downstream atom | 生成专属写作 Skill 骨架并校验；本 Skill 只写入内容。 |
| `lov-skill-publisher` | 发布 Skill | optional downstream atom | 仅在用户要求发布专属 Skill 时使用。 |
| `lov-human-writing` | 作者性与表层审计 | optional downstream atom | 可审计说明书或用专属 Skill 写出的文章。 |
| `lov-article-creator`、`lov-publish-wechat-article` | 公众号文章包与发布 | not composed | 属于专属写作 Skill 的下游，不在克隆流程内。 |

## Atomic Handoffs

```text
lov-wxmp-cli export / Markdown 目录
        │  research/wxmp-export, research/corpus
        ▼
lov-blogger-cloner
        │  style-pack/SLUG-vX（冻结）+ holdout-report + 风格说明书
        ▼
lov-skill-creator init  →  cloner.py package  →  validate
        │  lov-SLUG-style-writer 源码（不自动安装）
        ▼
optional: lov-skill-publisher
```

本 Skill 对风格包、留出检验和说明书的正确性负责；文章导出的完整性归 `lov-wxmp-cli`，Skill 骨架与安装归 `lov-skill-creator`，发布状态归 `lov-skill-publisher`。

## Overlap Decisions

- 不扩展 `lov-style-clone`：它是纯推理的一次性改写，加入账号级取样、哈希台账和留出检验会改变它的定位。两者在触发描述里互相分流。
- 不并入 `lov-media-cloner`：视频需要 FFmpeg、OCR、ASR 与 Remotion 模板，文字流水线只需标准库；共用方法，不共用代码。
- 不复制 `lov-human-writing` 的审计规则；本 Skill 的 `stylometry.py` 只做与训练集的度量带比对、原文重合与身份检测。

## Composition Decision

Single Skill。取样、度量、规则构建、冻结、盲测、留出与封装共用一个工作区和一套台账，拆成多个 Skill 会让冻结与封存失去约束力。相邻能力都通过文件交接，不是隐藏依赖。
