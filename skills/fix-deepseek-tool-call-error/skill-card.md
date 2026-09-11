# 任务急救 · Thread Rescuer · Skill Card

扫描本地 Codex rollout，定位 DeepSeek（provider=yoda、wire_api=responses）会话里
`No tool output found for tool call` 400 的事故现场，并给出恢复与预防方案。

# Owner

LovStudio（mark@lovstudio.ai）。

# License

MIT。本地只读诊断；不含远程发布，也不修改历史会话。条款见 `../LICENSE`。

# Use Case

面向在 Codex desktop 上通过 yoda provider 使用 DeepSeek 的个人与小团队：长任务或看图
任务跑到一半突然 400，整条 thread 再也接不上时，用它盘点事故、恢复任务、把规避前移。

# Deployment Geography

global。

# Requirements

无需凭据；Python 3.8+ 标准库；需要本地 `~/.codex/sessions` 与
`~/.codex/archived_sessions` 的读权限；无网络依赖。

# Known Risks

| 风险 | 缓解 |
| --- | --- |
| 把 400 当成模型故障反复重试，继续消耗额度 | 先跑扫描器确认受害调用与批次构成，再选择恢复方式 |
| 误以为存档缺记录而手改 rollout 文件 | 扫描器只读；恢复走重新加载或新 thread 接续 |
| 用关闭 view_image 的方式强推规避 | 预防清单明确禁止，只允许缩图、独占回合与外包看图 |

# References

- `SKILL.md`：主流程。
- `references/mechanism.md`：机制与 8 起事故证据。
- `references/prevention.md`：预防规则与可选配置。
- `references/recovery.md`：中毒 thread 的恢复手册。

# Skill Output

三类：事故清单（时间、thread、被拒调用、批次构成、变体、重复次数）、恢复方案（处置与
接续路径）、预防清单（规则与命令）。格式为 Markdown 或 JSON。

# Skill Version

0.1.0。

# Ethical Considerations

只读本地会话，不上传、不共享、不写入外部服务；报告保留最小必要片段，避免暴露凭据与
私人对话内容。

# User Cases

2026-09-11：同一天 6 条 thread 出现同类 400，其中 w-2 的信息图系列停在卡 03/05 的视觉
复核；用户先问原因，再要求“以后别再出现”。取证来自本机 rollout，产出是事故清单、
规则 51 与 MISC-29、以及新 thread 接续的恢复路径。详见 `cases/cases.json`。

# Dimension Map

| 维度 | 说明 | 证据 | 分数 |
| --- | --- | --- | --- |
| 取证正确性 | 事故定位是否与记录一致 | 扫出 8 起事故并与人工核对一致，含 01a08f9c 缺失调用为 exec_command | 4 |
| 恢复有效性 | 能否把任务接回可继续状态 | 新 thread 接续与归档重载已被使用；app 侧 A/B 仍待补 | 3 |
| 扫描效率 | 全量扫描耗时 | 约 150 MB rollout 全量扫描 47 秒 | 4 |

# Pricing Basis

免费。价值锚点是一次 400 会让整条 thread 报废且后续每轮秒级失败；交付边界是事故盘点、
恢复方案与预防清单；上游修复后或本机不再复现时复评。

# Distribution

付费渠道：无。免费渠道：github 与 lovstudio。当前状态：本地源就绪并可本地安装；
github 尚未推送；workbuddy、skillpay、lovstudio 均计划中。

