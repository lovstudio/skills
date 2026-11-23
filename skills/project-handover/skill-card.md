# 项目交接 · Project Handover · Skill Card

This human-readable card mirrors `skill-card.yaml`.

## Description

把进行中的项目整理成交给接手方的交接包：盘点体积与敏感信息，补读最新进展，按默认规则排除商务与私人信息，写交接文档和接手 Agent 的工作约定，生成文件清单与干净的 zip，并在全新目录从零安装、完整重建后与原产物比对验收。

## Owner

Lovstudio（https://lovstudio.ai）

## License / Terms

MIT。交接包内的项目内容归原项目权利人，Skill 不改变其版权与署名约定。

## Use Case

- **谁用**：把客户项目、内容制作或工程项目转给同事、合作方、外包继续做的个人与小团队；接手方常常也用 Agent。
- **输入**：项目目录、可读的沟通渠道、交出方对范围的要求。
- **任务**：盘点、补读最新进展、整理与脱敏、写文档、打包、全新目录验收。

## Deployment Geography

全球；本地 Agent 宿主，macOS 或 Linux。

## Requirements / Dependencies

- Python 3.9+（只用标准库）
- 比对音视频成品时需要 `ffmpeg`、`ffprobe`
- 重建验收需要被交接项目自己的工具链
- 依赖 `lov-branding-consistency` 审新写的交接文字
- 不需要任何凭据

## Known Risks and Mitigations

| 风险 | 缓解 |
| --- | --- |
| 把合同、联系人或私人笔记带给接手方 | 默认排除商务与私人类别，扫描个人信息与密钥，汇报被排除的内容 |
| 包里缺文件或命令写错，对方无法继续 | 清单逐项核对、文档路径逐项核对，全新目录从零安装并完整重建 |
| 遮盖路径时改坏运行文件 | 只改文本类生成物，疑似运行文件单独标出，回源工程修改 |
| 交接文档写入未经证实的内容 | 事实带日期与来源，推断标明，缺口单列 |

## References

- [Machine-readable card](skill-card.yaml)
- [Primary Skill instructions](SKILL.md)
- [交接范围与隐私](references/scope-and-privacy.md)
- [交接文档模板](references/handover-doc-template.md)
- [全新目录验收](references/acceptance.md)

## Skill Output

交接包文件夹（`HANDOVER.md`、`AGENTS.md`、`CLAUDE.md`、`MANIFEST.tsv` 与工程内容）、zip 归档、验收记录。校验：清单 verify、文档 check-refs、zip 自检、重建比对。

## Skill Version

0.1.0

## Ethical Considerations

交接包只在本地生成，由用户决定发给谁；默认不带合同、付款、分成、联系方式、私聊与账号；引用他人原话保留时间与提出人；不编造对方的确认或态度。

## LovStudio Evidence

### User Cases

见 [`cases/cases.json`](cases/cases.json)：一个进行中的客户制作项目中途移交，数十 GB 的工程整理为约 2 GB 的交接包，全新目录完整重建并与原成品比对通过。

### Dimension Map

交接完整性、隐私与商务隔离、全新目录可重建、盘点与打包效率；证据来自首个真实案例，尚未评分。

### Pricing Basis

见 [`pricing-card.yaml`](pricing-card.yaml)：免费入口，十次真实交接或收到接手方反馈后复评。

### Distribution

免费渠道 GitHub、Lovstudio：pending（2026-11-24，待目录合并、刷新、详情页回读与隔离试装）；付费渠道未选择。
