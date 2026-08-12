# Delivery Contract

成片交付由文件、参数、创意判断和状态证据共同组成。单独存在的 MP4 不代表已经发布。

## Required deliverables

- `final.mp4`：目标平台可接受的成片；
- `cover.png` 或 `cover-brief.md`：封面资产或可执行的封面方向；
- `edit-manifest.json`：源素材、时间线、保护段和混音策略；
- `final-probe.json`：视频、音频、时长、尺寸、帧率和编码信息；
- `audio-qc.json`：响度、峰值、采样率、声道和检查状态；
- `delivery-report.md`：人类可读的判断、证据和剩余缺口。

## Status fields

```yaml
render_status: passed
audio_status: passed
creative_status: passed
publish_status: not-requested
readback_evidence: []
```

状态解释：

- `render_status=passed`：文件存在、可解码，且媒体参数符合项目目标；
- `audio_status=passed`：原声保护、混音、响度和峰值检查通过；
- `creative_status=passed`：标题、封面、叙事结构和证据段完成；
- `publish_status=uploaded`：平台已接收文件，但线上可见性或回读尚未确认；
- `publish_status=published`：有平台回读证据支持，例如对象 ID、状态字段和成功标志；
- `publish_status=not-requested`：本次只制作成片，没有启动发布交接。

## Report minimum

报告至少记录：

1. 输入文件的可识别名称、源时长和源媒体参数；
2. 目标规格与实际输出规格；
3. 被压缩、被跳过和被保护的时间段；
4. BGM 文件名、ducking 规则和高潮段原声处理；
5. 视频解码、时间线、响度、峰值和人工回看的结论；
6. 标题、封面文案和未验证假设；
7. 发布对象、回读时间和原始状态字段（如果发生发布）。

## Handoff boundary

交给发布 Skill 时只发送已质检成片、封面、标题、简介/标签和交付报告。账号、Cookie、验证码和平台内部令牌留在运行时，不进入源目录或报告。发布 Skill 返回的状态与回读证据再写入交付报告的 `publish_status` 区域。
