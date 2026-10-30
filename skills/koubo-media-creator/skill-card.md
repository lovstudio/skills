# 口播短片 · Talking-head Short · Skill Card

> 版本 0.3.1 · MIT · Lovstudio.AI

## Description

输入一个主题，产出 AI 工具类竖版口播短片的带出处事实、过门禁的脚本、提词器、上屏证据与封面；作者照提词器竖拍一条口播后，
自动挑出每句最后念对的一遍、剪掉停顿，排成「上半屏证据、下半屏作者、字幕压在交界」的 1080×1920 成片，并交配乐、封面与质检报告。

## Owner

Lovstudio.AI · https://lovstudio.ai

## License / Terms

MIT。生成物著作权归作者；片中第三方网页截图须注明来源并遵守其使用条款。

## Use Case

- 受众：做 AI 工具、效率、开发类口播短视频的个人创作者与小团队。
- 场景：有选题、愿意自己出镜，但写稿、找证据、做提词、剪辑、做封面太耗时。

## Deployment Geography

全球可用；对齐与抠图的默认实现面向 macOS（Apple Silicon），其他系统可接外部 ASR 的逐字时间戳并自备抠图。

## Requirements / Dependencies

- Python 3.9+（numpy、pillow、mlx-whisper、opencc-python-reimplemented、jieba）、Playwright、FFmpeg/FFprobe。
- Node 20+、pnpm、Remotion 4.0.517；macOS swiftc + Vision。
- 依赖 Skill：`lov-branding-consistency`。
- 可选凭据（只从环境变量读）：`VOICENGINE_API_KEY`（样片占位配音）、`OPENROUTER_API_KEY`（AI 配乐）。

## Known Risks and Mitigations

| 风险 | 缓解 |
| --- | --- |
| 被用来冒充他人 | 出镜、声音、名字、Logo 只用作者本人；脚本门禁禁用参考博主口头禅；拒绝数字人冒充 |
| 口播出现不实或过期数字 | 含数字的句子必须引用带出处与核对日期的事实 |
| 剪辑吃字或保留念错的一遍 | 最长静音缝落刀；成片重转写吃字率 ≤ 3%；低分句人工复核 |
| 样片被当成片发布 | 样片画面带占位角标，状态单列为 animatic |

## References

- [SKILL.md](SKILL.md)
- [references/style-grammar.md](references/style-grammar.md)
- [references/script-format.md](references/script-format.md)
- [references/pipeline.md](references/pipeline.md)

## Skill Output

- `work/script.json`（脚本与事实）、`deliverables/teleprompter.html`、`script.md`、`shotlist.md`。
- `deliverables/<版本>/` 成片 MP4（1080×1920、30 fps、H.264 + AAC、bt709）与 3:4、16:9 封面 PNG。
- `qc/report-<版本>.json`、1 fps 联系表与封面缩略图。

## Skill Version

0.3.1（2026-10-30）

## Ethical Considerations

只复刻片型，不复刻人；不下载、搬运他人作品做素材；截图注明来源；AI 生成的配音、配乐、卡片在交付说明里列明；样片与成片状态分开。

## LovStudio Evidence

### User Cases

2026-10-28 样片：主题「给 Agent 一个主题，它把口播短片的前期全部备好」。12 句脚本门禁 0 ERROR；含两处故意念错的合成录音，
两处都选中后一遍、切点误差 ≤ 0.09 秒；40.7 秒样片 −16.0 LUFS、−1.5 dBTP、吃字率 0%；3:4 与 16:9 封面缩略图可读。
出镜与配音为占位，尚无作者真人录制的成片。

### Dimension Map

| 维度 | 证据 |
| --- | --- |
| 切点与文字正确 | 合成录音真值比对，12 句误差 ≤ 0.09 秒；成片重转写吃字率 0%、CER 0.027 |
| 片型还原度 | 风格语法来自 7 条代表作转写、接触表与 30 张封面；样片 1–3 秒换一次证据 |
| 作者投入 | 作者只需照提词器录一条口播 |

### Pricing Basis

免费开源（MIT）。作者于 2026-10-30 决定开源并停止付费销售；0.2.x 曾在 Lovstudio.AI 官网以一次性 1,394 Credits 发布。

### Distribution

- 免费渠道：GitHub 公开仓库（MIT）
- 付费渠道：无（已停止）
