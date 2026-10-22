# 励志视频 · Motivational Film

![version](https://img.shields.io/badge/version-0.2.1-blue)

把一个真实困境变成一个有理由的选择：原创口播、分镜、情绪和声音设计、素材权利账本，
以及能检查的制作包。不是他人电影/演讲混剪器，不承诺爆款，不把制作包冒充成片。
行动、休息、求助、回望均可成为落点；不把所有励志题材改成效率或胜利训话。

## 本地安装

将源目录放在自选位置，以共享skills入口链接为 `lov-motivational-media-creator`，再让当前宿主
skills目录以相对symlink指向共享入口。不要覆盖已有安装；核验realpath确实指向当前源。
官方目录安装使用 `npx -y lovstudio skills add motivational-media-creator --project`。
发布状态以官方目录与外部发布回执为准；本地链接不代表线上发布。

## ID迁移

canonical ID为 `lov-motivational-media-creator`，源目录为 `motivational-media-creator-skill`。
旧ID `lov-motivational-video` 及旧源路径仅作兼容入口，均指向同一实现；不产生第二套Skill。
Profile中的整个旧Skill节点已迁到新命名空间；旧节点只留历史备份，CLI使用旧ID时也读写新节点。
中文展示名及视频制作范围不变，0.2.0研究注记保持原样。

## 使用

- “做一条品牌励志视频，主题是卡在开始，给我口播、分镜和声音设计。”
- “把这次失败复盘做成90秒短片；只用这些已批准事实。”
- “Create an original motivational film from this brief.”

只下载字幕、软件教程或只发布不是触发任务；不会自动加鸡汤或外部上传。

## Profile

每次读取 [skill.yaml](skill.yaml) 声明的 `user-profile/v1`。
本地专用品牌写在 `skills.lov-motivational-media-creator.records.brand_name`，用户当前明确值优先。
语气、Logo、品牌事实与私有路径来自用户Profile/项目，不烘焙进可分发源。
用户直接给出的长期值由 `scripts/profile_store.py record --confirm` 保存。

## 制作示例与校验

真实创建任务衍生的 [原创演示](cases/original-demo/README.md) 是拟拍制作包，不是已经发生
的个人故事，也不是已录音或已渲染视频。素材、配乐与录制待办见示例权利账本。

```bash
python3 scripts/validate_production.py cases/original-demo/production.json
python3 scripts/validate_skill.py .
```

draft通过只代表结构通过。ready要求权利与素材到位，实际成片另需解码、连续播放抽听、
字幕与横竖版验收。使用者自行提供输出文件位置。
品牌视觉预览/成片须清晰使用批准的官方Logo；`brand-logo`须在时间线中，
缺失、未使用或生成替代均阻止ready/rendered-reviewed。无Logo只能是内部文字计划draft。

## 参考研究范围

[研究状态](references/reference-study.md)明确区分metadata、作者文字、实看片段与推断。
本版基于8条真实下载原片、英文VTT、完整解码和32张实际查看接触表，沉淀语义蒙太奇、
延迟兑现、多轮起伏和主题化收尾；不是全片连续观看或主观听音完成声明。
用户要求先下载再分析时严格按顺序完成，不用通用制作包替代原片研究。
原片、字幕和音乐不随包分发；网站访问受限时不以标题或缩略图冒充视听分析。

## 依赖和边界

Python 3.8+；Profile和制作包检查为标准库；Skill校验需PyYAML。
语义审校依赖 `lov-branding-consistency`。媒体执行器、yt-dlp、FFmpeg均按任务可选，
不自动下载大型素材、消费模型额度或发布。许可见 [LICENSE](LICENSE)。

## 质量门禁

[创作手册](references/creative-playbook.md)、[品牌边界](references/brand-adaptation.md)、
[作者完整性](references/authorship-integrity.md)、[组合记录](references/skill-composition.md)
共同约束真实事实、原创性、可拍性和权利安全。卡片维度未有用户评分，不虚构分数。
