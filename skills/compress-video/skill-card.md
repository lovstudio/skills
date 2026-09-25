# 视频瘦身 · Video Shrink · Skill Card

This human-readable card mirrors `skill-card.yaml`. It is a release record, not
an implementation note. A reviewer should understand the Skill without opening
its source.

## Description

把指定视频压到尽可能小且肉眼看不出明显损失的 MP4。默认 libx265 CRF 28、保留分辨率
与帧率，原文件不动；可选质量档、目标体积、VMAF 画质门禁与替换原文件模式。

## Owner

Local skill contributors；联系本地 Skill 源目录维护者。

## License / Terms

MIT。被压缩的视频及其内容权利保持原归属。

## Use Case

面向需要把课程实录、屏幕录制、相机素材压到可分享体积的创作者与团队。输入是一个或
多个视频文件，输出是压缩后的 MP4 与统计结果。

## Deployment Geography

全球；本地运行，无网络请求。`--fast` 与废纸篓式替换依赖 macOS。

## Requirements / Dependencies

- Python 3.9+，脚本仅使用标准库
- FFmpeg / FFprobe，含 libx265；libx264、libsvtav1、libvmaf 按开关需要
- PyYAML，仅本地校验脚本需要

## Known Risks and Mitigations

- 画质损失超出预期：默认 CRF 28 实测 VMAF 93.5，`--min-vmaf` 自动重编，缩放只在要求时做。
- 替换误删：默认不替换，`--replace` 先进废纸篓，`--permanent` 才直接删除；异常时原文件不动。
- 输出损坏：先写 `.part.mp4`，时长偏差即丢弃，失败清理。
- 硬件编码画质差：仅 `--fast` 开启，文档给出同体积 VMAF 对照。

## References

- [Machine-readable card](skill-card.yaml)
- [Primary Skill instructions](SKILL.md)
- [Encoding guide](references/encoding-guide.md)

## Skill Output

压缩后的 MP4（HEVC / H.264 / AV1）；stderr 摘要与 `--json` 结果给出源与结果体积、
比例、节省量、用时、VMAF、所用编码参数与完整 ffmpeg 命令，`replaced` 与
`original_moved_to` 字段说明原文件去向。

## Skill Version

0.1.0

## Ethical Considerations

只读取用户指定的文件；不上传、不采集内容；替换模式需要用户明确授权且默认可从
废纸篓恢复。

## LovStudio Evidence

### User Cases

See [`cases/cases.json`](cases/cases.json). Every case must show Input → Prompt → Output.

### Dimension Map

压缩率、画质保真、原文件安全、可控性四个维度，证据分别来自真实片段压缩结果、
VMAF 测量、替换与门禁测试、参数映射测试；分数状态见机器可读卡片。

### Pricing Basis

See [`pricing-card.yaml`](pricing-card.yaml). 免费：纯本地 FFmpeg 工具，价值在于
把参数选择与安全门禁固化。

### Distribution

免费渠道：MIT source。目前只完成本地源验证，尚未发布到 `github`、`lovstudio`、
`workbuddy` 或 `skillpay` 任一渠道。
