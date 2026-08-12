# Skill Group Composition

这个记录把相邻媒体能力和本 Skill 的最终验收边界分开，避免因为名称相近而形成隐藏依赖。

## Nearby Skills Inspected

| Skill | 实际输入 → 输出 | 关系 |
| --- | --- | --- |
| `FFmpeg Video Editor` | 自然语言编辑请求 → 单条 FFmpeg 命令 | 可参考的上游原子；本 Skill 负责完整流程、EDL、音频门禁和报告，不只返回命令。 |
| `lov-video-chapter` | SRT/视频 → 章节项目、透明层、烧录视频和编辑包 | 下游可选能力；接收已确认的成品或字幕，不参与本 Skill 的核心剪辑判断。 |
| `lov-subtitle-freedom-skill` | 视频/SRT + 学习者 Profile → 保持时间轴的 SRT/ASS | 下游可选能力；只在明确要求学习字幕时交接。 |
| `lov-image-creator` | 图像 brief → PNG、HTML 或外部模型 Prompt | 上游/下游均可；本 Skill 输出封面方向 JSON 或文字 brief，图像 Skill 负责新图资产。 |
| `lov-media-fetch` | 检索需求 → 已下载并核验的本地媒体 | 上游可选能力；只负责取得素材，不负责剪辑与成片验收。 |
| `lov-publish-wechat-channels` | 已质检媒体 → 发布状态与平台回读 | 下游可选能力；接收本 Skill 的 MP4 和交付报告，最终发布状态由发布能力负责。 |

## Atomic Handoffs

- `SOURCE_VIDEO`、音频和字幕流 → `media_probe.py` → `source-probe.json`：本 Skill 自己拥有输入完整性判断。
- EDL JSON → `timeline_check.py` → `timeline-check.json`：本 Skill 自己拥有时间线不重叠和 protected segment 门禁。
- 成片 MP4 → `media_probe.py`、`audio_qc.py` 和 FFmpeg decode smoke test → `final-probe.json`、`audio-qc.json`：本 Skill 自己拥有渲染与音频验收。
- 已质检 MP4 + 交付报告 → `lov-publish-wechat-channels`：发布 Skill 拥有账号交互、发布和线上回读；本 Skill 只记录交接状态。
- 已确认成片或字幕 → `lov-video-chapter` / `lov-subtitle-freedom-skill`：这些能力拥有章节或学习字幕输出；本 Skill 不复制其专门逻辑。
- 封面方向 brief → `lov-image-creator`：图像能力拥有生图/渲染；本 Skill 负责封面在标题、主题和成片证据中的位置。

## Overlap Decisions

- 与 `FFmpeg Video Editor` 有命令级重叠，保留其作为参考，不把本 Skill 缩减成命令生成器，因为用户要的是从素材到成片的完整闭环。
- 与 `lov-video-chapter`、`lov-subtitle-freedom-skill`、`lov-image-creator` 只在文件级交接，不复制章节、学习字幕或生图实现。
- 与 `lov-media-fetch` 的边界在“素材已可读”；媒体获取失败时交回上游，不在此 Skill 内加入下载器。
- 与 `lov-publish-wechat-channels` 的边界在“成片已通过质检”；发布失败或回读缺失不得倒写成片状态。

## Composition Decision

选择 **Single Skill**。用户可见的结果是一个经过编辑、混音和质检的成片，扫描、剪辑规划、渲染、音频检查和交付报告共享同一份项目上下文；它们拆成独立 Skill 只会增加交接成本。相邻 Skill 通过明确的文件与状态交接保持可选，不作为源目录外的硬依赖。
