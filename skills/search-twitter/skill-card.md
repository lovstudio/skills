# Skill Card — lov-search-twitter

## Description

从人物、账号、关键词、X 链接、status ID 或截图出发，建立候选清单并恢复可核验的逐字正文；输出同时保留截图哈希、来源级别、冲突和未恢复项。

## Owner

LovStudio Skills，维护联系 `maintainers@lovstudio.com`。

## License / Terms

Skill 源码使用 MIT。帖子、截图和媒体内容仍归原权利人所有；使用者须遵守平台条款、版权、隐私与合理使用边界。

## Use Case

面向研究者、记者、内容编辑与自动化 Agent。支持公开人物或账号的当前/旧 handle、关键词、原帖 URL、status ID、转载截图和时间范围；目标是逐字汇总与证据对账，不负责判断帖内指控是否为真。

## Deployment Geography

可在全球本地 Agent runtime 使用；广泛发现能力取决于运行环境可访问的网页、图片搜索和归档服务。

## Requirements / Dependencies

Python 3.9+ 标准库。公开渲染器与网页归档需要网络；广泛发现需要 web/image search 或浏览器；OCR 可选。默认零登录，获用户明确授权后才可选择 `twscrape` 做完整账号枚举。

## Known Risks and Mitigations

- 搜索索引可能漏掉中文 App 内的转帖截图：网页和图片搜索并行，特别覆盖中文媒体、微博、微信公众号、Telegram、论坛和转载页，并报告查询与缺口。
- 转载、OCR、摘要和空壳归档可能被误认为原文：使用七级 provenance，逐字正文、OCR、翻译、摘要分开交付。
- 两个公开渲染器可能截断或冲突：保留所有变体，只有 URL 展开或空白差异才合并；失败后查询精确归档。
- 内容可能涉及版权、隐私或未经证实的指控：只处理公开或获授权内容，保留归因，不把“某人发过”改写为“内容已经证实”。

## References

- [Machine-readable card](skill-card.yaml)
- [Primary Skill instructions](SKILL.md)
- [Evidence model](references/evidence-model.md)
- [Discovery playbook](references/discovery-playbook.md)
- [Composition record](references/skill-composition.md)

## Skill Output

输出候选/原帖索引、逐字正文汇总、截图证据 manifest、冲突与未恢复清单。机器格式为 JSON/JSONL，人读格式为 Markdown；图片保留原始字节和 SHA-256。验收要求每项与候选清单对账，并把原文、OCR、媒体引文、摘要和翻译分开。

## Skill Version

0.1.0

## Ethical Considerations

不绕过私密账号、封禁、登录墙、付费墙、速率限制或平台保护。会话与凭据只存在于 OS 凭据存储或当前进程，不写入 Profile、源码、测试和报告。恢复公开发言不等于认同或证实发言内容。

## LovStudio Evidence

### User Cases

[cases/cases.json](cases/cases.json) 记录了当前真实恢复任务：现账号 7 个已知 ID 的 live recovery、旧账号 8 个已知 ID 的归档与截图证据对账。

### Dimension Map

机器卡包含逐字正确性、证据完整性、发现覆盖和恢复效率四个维度及其可复核证据。

### Pricing Basis

[pricing-card.yaml](pricing-card.yaml) 说明本地能力免费，以及托管索引、付费 API、团队仓库和人工核验的边界。

### Distribution

免费分发目标为本地 Agent、GitHub 与 LovStudio。各渠道的 live/verified 状态由
Publisher 的外部发布记录维护，不写进 canonical source。
