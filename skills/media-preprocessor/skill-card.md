# 视频素材精整 · Video Prep · Skill Card

## Description

对实录做连续画质增强、内容取舍和语义分段，输出可回溯素材库。

支持将已增强视频、原片时间码、哈希与审阅状态交给 `lov-media-creator`，并提供可直接打开 MP4 的列表；下游负责独立切片、精剪和成片包装。

## Owner

Local skill contributors，联系本地源码维护者。

## License

MIT，源素材权利不变。

## Use Case

课程、沙龙与活动实录的剪辑前整理。

## Deployment Geography

本地运行，地域不限。

## Requirements

Python 3.9+、NumPy、OpenCV、FFmpeg/FFprobe、PyYAML、宿主视觉与时间戳语音证据。

## Known Risks

静音误删、增亮失真、中断混用；通过联合判断、样片和契约续跑处理。

## References

[主流程](SKILL.md)、[增强](references/enhancement-contract.md)、[分段](references/segmentation-contract.md)。

## Skill Output

MP4 分段、JSON 源映射和本地 HTML 审阅页。

## Skill Version

0.1.0，2026-09-06。

## Ethical Considerations

不伪造对白、演示、动作或课件；原片只读，私有素材不随源码分发。

## User Cases

[真实案例](cases/cases.json)；合成测试不是用户案例。

## Dimension Map

内容完整性、连续画质、源时间回溯、长任务恢复；证据见 skill-card.yaml，无虚构评分。

## Pricing Basis

本地开源流程免费，缺少人工对照和完整账单，不声称具体节省比例。 含分析、判断契约、增强和导出；模型、存储或外部转录可另计，不含发布。

## Distribution

共享 Agent/Codex 本地安装；workbuddy、skillpay、github、lovstudio 均未发布。
