# 励志短片 · Claude 版 · Motivational Film (Claude edition) · Skill Card

`lov-motivational-media-creator-claude-version` · Motivational Film (Claude edition)

This human-readable card mirrors `skill-card.yaml`.

## Description

把一个人或团队真实的倒下与起来做成 2–6 分钟励志短片：按参考片实测的节奏选片型、排节拍、写旁白、写时间线并体检，渲染后再测一遍成片，与参考片区间对照。渲染本身交给用户的剪辑执行器。

## Owner

本地 Skill 维护者；通过源目录的维护记录反馈。

## License / Terms

MIT。只涵盖本 Skill 的指令、脚本和由测量得出的数字；不授予参考视频、演讲、音乐、Logo 或任何第三方素材的使用权。

## Use Case

- 受众：做品牌片、人物片的创作者与剪辑协作者。
- 场景：有一个真实的人或团队、一段真实的低谷与回来，想做成有节奏、有出处的短片；或想知道一条已剪好的励志片节奏哪里不对。
- 任务：拆参考片节奏；节拍表、旁白稿与时间线；时间线体检；成片复测。

## Deployment Geography

Global；本地 Agent Skills 宿主。

## Requirements / Dependencies

- Python 3.8+ 标准库，FFmpeg 与 ffprobe；PyYAML 只用于 Skill 校验。
- `lov-branding-consistency`（读者可见文案的品牌门禁）。
- 渲染执行器可选：用户的 Remotion 工程或 `lov-media-creator`。
- 无需凭据。下载参考片若需登录，只在用户当次授权范围内复用已有会话。

## Known Risks and Mitigations

| 风险 | 缓解 |
|---|---|
| 把参考片素材直接拼进新片 | 参考只提供节奏；素材账本记权利；未清权最高到 review |
| 编造原话、内心独白或因果 | 事实账本、作者性约束；体检按 claim 状态拦截 |
| 自杀、自伤题材处理不当 | 标记敏感后必须有安全审查与核实的求助信息 |
| 把机器复测当作看过片 | 五个状态分开报告，未经人审要写明 |
| 样本小导致区间过窄 | 偏出只警告；可用自己的参考片重建包络 |

## References

- [Machine-readable card](skill-card.yaml)
- [Primary Skill instructions](SKILL.md)
- [参考片研究](references/reference-study.md)

## Skill Output

节奏档案与包络、节拍表与旁白稿、时间线与体检报告、成片复测报告；JSON 与 Markdown。不含渲染好的视频。
校验：`check_timeline.py` 门禁与 9 个负例；`study_reference.py` 对 8 条参考片和 1 条真实成片的测量；`scripts/validate_skill.py`。

## Skill Version

0.1.0

## Ethical Considerations

不搬运第三方演讲、影视与音乐；不模仿真人声音；不编造亲历或原话；不羞辱观众、不歌颂透支、不承诺成功；涉及自杀或自伤时按安全报道方式处理并附求助信息；可识别的旁人未经同意要裁切或打码。

## LovStudio Evidence

### User Cases

见 [`cases/cases.json`](cases/cases.json)：

1. 从 8 条 TheMiro0r 原片建立节奏包络（本次创建任务）。
2. 体检《为什么是梅西》v1.0 的时间线与成片（创建时自测，只读）。

### Dimension Map

证据来源、门禁有效、成片诊断、作者性与安全。四项都还没有用户评分，证据见 `skill-card.yaml`。

### Pricing Basis

见 [`pricing-card.yaml`](pricing-card.yaml)。免费，本地自用，与另一版本并行比较。

### Distribution

`workbuddy`、`skillpay`、`github`、`lovstudio` 均未发布。本地已安装。
