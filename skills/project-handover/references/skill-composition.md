# Skill Group Composition

## Nearby Skills Inspected

- `lov-repo-takeover`：把已有克隆连接到用户自己的 GitHub 仓库并保留来源。处理的是“接手后怎么挂仓库”，不整理交接内容。**not composed**（相邻，方向相反）。
- `lov-checkpoint`：根据 git 差异记录项目里程碑与后续事项，给自己看，不移交给别人、不打包。**not composed**。
- `lov-agent-instructions`：诊断、完善项目的 Agent 指令文件。交接时的 `AGENTS.md` 改编规则写在本 Skill 的模板里；如果用户想进一步打磨接手方的约定文件，可在交接包生成后交给它。**downstream atom（可选）**。
- `lov-wdb-cowork`：读本机微信会话，补读群里的最新进展、意见和新成员。**upstream atom（可选）**：交付物是事实摘要，本 Skill 只摘取交接需要的事实，聊天临时文件按它的规则清理。
- `lov-tencent-meeting-cowork`、飞书文档与群消息类能力：补读会议结论、在线文档和群消息。**upstream atom（可选）**，同上。
- `lov-branding-consistency`：审新写的读者可见文字。交接文档属于成文内容，按 SKILL-18 列为顶层依赖；它不改原文引用、群记录和数据。**dependency**。
- `lov-media-creator` 等制作类 Skill：交接的项目可能是它们产出的工程，本 Skill 不接管制作，只把工程和它们的使用方法写进交接文档。**not composed**。

## Atomic Handoffs

| 交接 | 物件 | 边界 | 验收归属 |
| --- | --- | --- | --- |
| 补读最新进展 → 本 Skill | 带时间、提出人的事实摘要 | 上游只读取和摘要，不写交接文档 | 本 Skill 在交接文档里标来源与缺口 |
| 本 Skill → 品牌审校 | `HANDOVER.md`、`AGENTS.md` 新写的段落 | 只审新写文字，引用与数据不动 | 本 Skill 回读审校后的文档并重出清单 |
| 本 Skill → 指令文件完善（可选） | 交接包里的 `AGENTS.md` | 用户另行要求时才调用 | 指令文件 Skill 自己的校验 |

## Overlap Decisions

没有现有 Skill 产出“可交给他人、经全新目录重建验证的交接包”。`lov-checkpoint` 和 `lov-repo-takeover` 的结果不同，不扩展它们，避免把“自用记录”“仓库接管”和“对外移交”混在一个入口。

## Composition Decision

Single Skill：盘点、补读、定范围、写文档、打包、验收都服务于同一个交付物，且后一步依赖前一步的上下文（例如验收发现的坑要写回文档）。脚本只是确定性工具，不构成可以单独触发的阶段，所以不拆成 Kit。
