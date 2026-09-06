# Skill Card — lov-video-moments

## Description
从课程或活动视频挑选真实照片 moments，完成纪实美化、组图标准化与可回溯交付。

## Owner
Local skill contributors；联系本地 Skill 源目录维护者。

## License
[MIT](LICENSE)。视频和照片权利保持原归属。

## Use Case
课程讲师、活动组织者与记录者，从长实录整理朋友圈图片。

## Deployment Geography
本地运行，地域不限；宿主模型服务的可用地域由服务方决定。

## Requirements
Python 3.9+、Pillow 10.1+、FFmpeg/FFprobe、PyYAML、宿主视觉能力。摄影调色需要 NumPy；编辑方法沿用用户选择并遵循宿主规则。新增文案受 lov-branding-consistency 门禁约束。

## Known Risks
稀疏取样可能漏掉短暂瞬间；生成编辑可能改脸或改字；黑暗源片不一定可恢复细节。逐张视觉验收，保存源帧，明确覆盖范围，失败不伪报完成。

## References
[主流程](SKILL.md)、[筛选规则](references/selection-policy.md)、[美化契约](references/image-contract.md)、[组合决策](references/skill-composition.md)。

## Skill Output
1–9 张 JPEG/PNG、总览、本地 HTML 审阅页与 JSON 时间码/哈希清单。默认不加图上文案，不自动发布。

## Skill Version
0.3.0，2026-09-07。

## Ethical Considerations
不编造授课金句或参与者反应；人物与课件保真；私有素材不随 Skill 分发，公开传播另循授权。

## User Cases
[真实案例](cases/cases.json)。合成 CLI 测试只证明工程行为，不是用户案例。

## Dimension Map
可溯源、纪实保真、组图分享价值、大文件中断恢复四个维度，证据路径见 [机器记录](skill-card.yaml)。当前无外部评分，不填虚构分数。

## Pricing Basis
源码免费，0 Credits；宿主模型、转录或编辑服务可能产生独立费用。尚无受控耗时对照和完整账单，详见 [定价依据](pricing-card.yaml)。

## Distribution
MIT 源码分发。具体渠道发布与验证状态保存在独立 Publisher 记录，以仓库 Release 和官网实际页面为准。
