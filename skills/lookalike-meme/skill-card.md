# 撞款表情包 · Lookalike Meme · Skill Card

This human-readable card mirrors `skill-card.yaml`.

## Description

把一位真人的现场照片和一张参考形象图做成网感撞款表情包：AI 以本人照片为参考画原创 Q 版卡通并模仿参考姿势，HTML 排版出亮色网点放射线背景、白边歪斜贴纸和单个大标题的 1080×1440 PNG，另附卡通 PNG。

## Owner

LovStudio（https://lovstudio.ai）。

## License / Terms

源码 MIT。成品中的真人肖像归本人，参考角色版权归原权利人；含第三方版权角色的成品仅适合私下或群内使用。

## Use Case

内容创作者或社群运营在活动、聚会或节目里发现有人和某个卡通角色撞款，给出本人照片或视频帧、参考形象图和一句标题，得到可发群的对比图。

## Deployment Geography

全球；在本地 Agent 宿主运行，卡通步骤调用 OpenRouter。

## Requirements / Dependencies

- `OPENROUTER_API_KEY`（仅卡通步骤，从环境变量读取）
- Python 3.9+、Pillow；Chrome / Chromium / Edge；得意黑 SmileySans；ffmpeg（仅视频取帧）
- `lov-branding-consistency`（标题文案语境检查）

## Known Risks and Mitigations

- 未经同意使用真人肖像：同意是第一道门禁，未确认不做。
- 本人照片上传第三方：开工前告知，照片缩到长边 1024，拒绝上传时只做排版。
- 复刻版权角色：参考角色图不交给生图模型，提示词禁止模仿；交付时标注仅限私下或群内使用。
- 费用失控：生图前报价，每次调用写入 `ledger/costs.jsonl`，网络失败不自动重试。
- 中文字错乱：所有中文由 HTML 排版。

## References

- [Machine-readable card](skill-card.yaml)
- [Primary Skill instructions](SKILL.md)
- [版式规格](references/layout.md)

## Skill Output

1080×1440 PNG 对比图、1024×1024 PNG 卡通、可选可编辑 HTML。参数：标题、1–3 张贴纸（可 contain）、配色、姿势与特征描述。验收：尺寸正确、标题与贴纸完整、卡通像本人且无文字、账本有记录。

## Skill Version

0.1.0

## Ethical Considerations

只在本人同意时制作；不用于嘲讽外貌、骚扰、冒充或商业广告；参考角色只用用户提供的原图。

## LovStudio Evidence

### User Cases

见 [`cases/cases.json`](cases/cases.json)：一位真人与一个卡通角色的撞款图。

### Dimension Map

版式还原、像不像、成本与耗时、同意与版权门禁，证据见 `skill-card.yaml`。

### Pricing Basis

见 [`pricing-card.yaml`](pricing-card.yaml)：免费，生图费用由用户自己的额度承担。

### Distribution

免费渠道 GitHub、Lovstudio：pending（2026-11-24：目录 PR 准备中，官网详情页与试装未验证）；付费渠道未选择。
