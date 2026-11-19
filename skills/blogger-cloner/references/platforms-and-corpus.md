# 语料、平台与选样

## 公众号（已支持）

1. 用 `lov-wxmp-cli` 确认账号已缓存且有正文：`accounts` 看 `article_count`，`articles '账号名'` 看 `has_content`。缓存不足时，由该 Skill 在用户授权下 `fetch --content` 补采；本 Skill 不直接抓取微信正文。
2. 导出：`lov-wxmp-cli export '账号名' --out DIR/research/wxmp-export --format all --body md`。导出目录含 `manifest.json`（`lov-wxmp-export/v1`）与 `index.json`（带 `content_md` 的文章和 `account` 信息）。
3. 导入：`cloner.py ingest --source wxmp-export --path DIR/research/wxmp-export`。正文不足 200 个字词单位的文章记为 `has_body: false`，不进入取样池。账号名、别名和签名写进 `research/brand/account.json`，后续作为身份标识用于防冒充。

## 其他平台（通过文字目录接入）

小红书图文、X/Twitter、知乎、博客、视频号/抖音/B 站的口播转写，都先由对应能力拿到文字，再整理成 Markdown 目录：

```text
---
id: 平台作品 ID（ASCII）
title: 标题
date: 2026-05-01
link: 原文链接
---
正文，一段一行。
```

用 `cloner.py ingest --source files --path DIR --platform xiaohongshu` 导入。下载交给 `lov-media-crawler`，转写交给 `lov-voice2srt` 或已有转写；视频的画面与剪辑风格交给 `lov-media-cloner`，本 Skill 只分析文字。

短帖平台（X、小红书）单条很短，度量带会很宽：样本量至少 30 条，必要时按“线程/合集”合并成一篇再导入，并在 `--note` 写明。

## 基线语料

标志短语按“相对基线的倍率”排序，没有基线时只能按跨篇频次排序，赛道通用词会混进来。基线选 3–6 个同赛道、同平台的其他账号（媒体号与个人号混合），总量 50 篇以上即可，用 `--role baseline --label 账号名` 导入。基线只参与短语倍率，不参与规则与证据。

## 格式期

先看候选清单的日期分布和标题形态。账号改过版（标题风格、栏目、结尾固定段换了）时只取最近一个格式期，用 `--era-from/--era-to` 限定，并在 `--era-note` 写判断依据。跨格式期混选会把两种风格平均成一种不存在的风格。

## 选样与留出

- **时机**：`select` 与 `freeze-split` 必须在读任何正文之前完成。只看 `candidates` 给出的标题、日期、篇幅和标记。
- **排除**：`listing_or_notice`（一览、招聘、抽奖、声明）、`short`、转载与他人署名的文章默认排除，用 `--exclude` 写明。
- **分层**：按标题初判子类型（新闻解读、实测推荐、教程、自家产品、观点方法论……），每层都有训练样本；留出尽量各取一篇主要子类型。
- **数量**：训练 12–20 篇为宜，至少 3 篇；留出约 15–20%，至少 1 篇。也可 `--holdout-count K` 按日期均匀取留出。
- **理由**：分层依据写进 `--note`，会进入 `sources.json` 和风格包的 `provenance`。

## 不做

不绕过付费、私密或已删除内容；不替用户登录；不收集评论区与读者的个人信息；不把导出的原文发到任何外部服务。
