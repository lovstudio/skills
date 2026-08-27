# Skill Card — lov-search-file

This human-readable card mirrors `skill-card.yaml`. It is a release record, not
an implementation note. A reviewer should understand the Skill without opening
its source.

## Description

从本机 AI 对话记录追溯图片、文档和其他交付文件，返回仍然存在的候选路径、来源
会话、证据片段与存储耐久度。

## Owner

LovStudio（contact: lovstudio）

## License / Terms

MIT。免费使用；只读访问用户自己的本地对话记录与文件系统。

## Use Case

面向记得对话主题或一句原话、却忘记文件名与保存位置的用户。输入查询词、可选
session ID 与搜索根，输出按证据和耐久度排序的现存文件候选。

## Deployment Geography

全球；在用户自己的 macOS 或 Linux 本机运行。

## Requirements / Dependencies

Python 3.9+。ripgrep 推荐但可选；不需要网络、API 或凭据。

## Known Risks and Mitigations

- 原始输入可能被误认成最终交付：结合消息角色、最终回答标记与输出关键词评分。
- transcript 含私密信息：仅本地处理，缓存权限 `0600`，可用 `--no-cache` 禁用。
- 临时文件可能过期：每次实时 `stat`，默认过滤不存在路径，并降低临时目录权重。

## References

- [Machine-readable card](skill-card.yaml)
- [Primary Skill instructions](SKILL.md)

## Skill Output

JSON 或结构化文本候选列表，包含绝对路径、存在性、大小、修改时间、文件类型、
来源 session、transcript、短证据、分数与存储耐久度。默认每条返回路径都在本轮
文件系统回读中存在。

## Skill Version

0.1.0

## Ethical Considerations

只检索用户自己的本地数据，不上传 transcript 或文件，不绕过加密或访问控制；
不存在的历史路径不会被表述为仍可用文件。

## LovStudio Evidence

### User Cases

See [`cases/cases.json`](cases/cases.json). Every case must show Input → Prompt → Output.

### Dimension Map

The machine-readable card contains the dimensions, evidence, and score status.

### Pricing Basis

See [`pricing-card.yaml`](pricing-card.yaml). Free Skills still explain their value,
boundary, and review trigger.

### Distribution

0.1.0 的免费分发目标为本地安装、GitHub 公开源码与 LovStudio 官网目录。GitHub
仓库、Release、目录合并、缓存刷新和官网回读全部完成后，才可把后两项描述为 live。
