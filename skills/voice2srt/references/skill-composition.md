# Skill Group Composition

This record is required for every generated Skill. It prevents adjacent Skills
from becoming accidental duplicates or hidden dependencies.

## Nearby Skills Inspected

- `lov-personal-vocabulary`：个人词库的 canonical store、应用适配与同步 owner。
  本 Skill 只消费 canonical `vocabulary.json` 或 OpenLess adapter JSON，不复制词库
  管理逻辑，也不写回命中次数。
- `lov-media-creator`：从素材到可发布成片的 owner。本 Skill 输出 SRT/JSON，后者
  决定 EDL、字幕版式、烧录、混音、响度与最终渲染。
- `lov-subtitle-freedom-skill`：已有字幕的学习注释与可选 ASS 艺术层 owner；其
  SKILL 明确把 speech recognition 视为独立任务，因此不在此实现学习注释。
- `lov-video-chapter`：章节规划、渲染与导出 owner，不负责语音转写。
- `FFmpeg Video Editor`：通用媒体裁剪与编码能力；本 Skill 仅使用 FFmpeg 做确定性
  音频预处理，不把通用剪辑流程作为隐藏依赖。

## Atomic Handoffs

1. 上游：`lov-personal-vocabulary` → canonical `vocabulary.json`；验收边界是合法
   JSON、启用词可解析、大小写去重。用户也可直接给 OpenLess `dictionary.json`。
2. 核心：`lov-voice2srt` → `transcript.srt`、`transcript.json`、`transcript.txt`、
   `report.json`；验收边界是时间轴有效、凭据不落盘、成本与 provider 可审计。
3. 下游：`lov-media-creator` 接收 SRT/JSON；其验收从剪辑时间轴、视觉版式、原声
   保护与成片质检开始。本 Skill 不宣称成片完成。
4. 可选下游：`lov-subtitle-freedom-skill` 接收最终 SRT 并保持 cue 时间轴添加学习
   注释；本 Skill 不要求其安装。

## Overlap Decisions

- 词库解析兼容 canonical/OpenLess 两种 artifact shape，但词库生命周期完全留给
  `lov-personal-vocabulary`。
- 字幕格式验证属于本 Skill；字幕审美、学习注释和烧录分别留给相邻 Skill。
- OpenLess 的 provider、模型、热词格式可作为运行配置来源；本 Skill 不依赖
  OpenLess 应用进程，也不复制它的 UI、历史记录或润色管线。

## Composition Decision

这是 Single Skill：用户可见目标始终是“音视频 → 可剪辑字幕包”，词库适配、云端
调用与 SRT 校验都是同一结果的内部阶段，不构成独立用户产品。所有 sibling Skill
都通过文件交接且保持可选，不是隐藏依赖。
