# Changelog

## 0.2.0 — 2026-11-17

- 升级为所有视频 Skill 共用的片尾（media end）：作者 2026-11-17 要求把采访片结尾的 Logo 片段提取为手工川视频的统一片尾模板。
- 新增 `scripts/media_end.py`：`make` 读共享 Profile 的 `preferences.video_outro`，校验官方 SVG 的 sha256，一次生成
  `spec.json`、`timing.json`、`sting.wav` 与 `outro.json`；`mix` 把音效按帧并进整片混音，限幅、定响度，并复测编码后的真峰值，
  不达标自动压低限幅重来。替代各集各写一份的 `mix_with_sting.py`。
- SKILL.md 新增「共享片尾（Media End）」一节；User Profile 解析顺序加入 `preferences.video_outro`；与视频 Skill 的关系从
  「可选下游」改为「默认片尾」。
- 实测：按记录生成的 `timing.json`、`sting.wav` 与参考采访成片逐字节一致；在一条约 2 分钟的口播样片上并入后 −16.1 LUFS、−3.4 dBTP。

## 0.1.0 — 2026-10-22

- 首个版本：从《如何用 AI 制作视频》v0.2（2026-10-21）的片尾品牌动画抽出的独立 Skill「品牌片尾 · Logo Sting」。
- `scripts/logo_spec.py`：官方 Logo SVG → `logo-sting-spec/v1`。路径数据原样拷贝，精确包围盒，平移/等比缩放变换烘焙，
  拒绝活字、徽章/反白锁定、非路径形状和其它变换；`--mark`、`--order` 调整分组，`--preview` 输出分组预览 SVG。
- `scripts/sting_timing.py`：帧表 `logo-sting-timing/v1`，默认 100 bpm 网格，或用 `--beats` 跟随宿主配乐的拍点。
- `scripts/sting_audio.py`：从帧表确定性合成片尾音效（48 kHz 立体声，−1 dBTP）；参考帧表下与原片音效逐字节一致。
- `assets/remotion/LogoSting.tsx`：自包含的 Remotion 组件，适配竖版、横版、方形与任意 fps；导出类型直接接受 JSON import。
- `scripts/render_sting.py` 与 `assets/remotion-template/`：渲染独立 H.264/AAC 片段（9x16、16x9、1x1、4x3），ffprobe 自检。
- 文档：`references/spec-contract.md`（数据合同）、`references/integration.md`（Remotion 与 FFmpeg 接入、混音、卡拍）、
  `references/qc.md`（关键帧、品牌安全、声音与参考结果）、`references/skill-composition.md`（相邻 Skill 与交接）。
