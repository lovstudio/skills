# 人像大片 · Spectacular Portraits · Skill Card

This human-readable card mirrors `skill-card.yaml`. It is a release record, not
an implementation note. A reviewer should understand the Skill without opening
its source.

## Description

将原照片修成保留本人、服装与姿态的环境人像，支持头像裁切、真实对比图和复刻 Prompt。

## Owner

contributors；通过当前宿主向本地源码维护者反馈。

## License / Terms

代码和指令采用 [MIT](LICENSE)。用户照片与第三方参考素材不因此获得再分发许可。

## Use Case

面向有旅行、户外或城市人像原图的用户。可附风格参考；输出照片或头像，不是职业证件照、
插画重绘、Photoshop 自动化或申请文书。

## Deployment Geography

全球可用的本地 Agent 工作流；图像服务的可用区域由宿主提供方决定。

## Requirements / Dependencies

原生看图与图像编辑能力；Python 3.9+、PyYAML 用于本地校验，Pillow 用于可选对比。
`lov-branding-consistency` 审校说明与标签。Skill 不扫描或读取 API 密钥。

## Known Risks and Mitigations

- 身份漂移：原图为身份来源，逐轮检查五官、神态、衣服、饰品、手部与姿态。
- 参考内容串入原图：分清原图、风格参考、否定稿与选定成片，限定可借鉴维度。
- 场景被重构：默认只做写实后期；获授权的艺术化改动明确披露。
- 虚假对比：用真实文件排版、来源哈希与回读验证，不重绘 BEFORE 面板。

## References

- [Machine-readable card](skill-card.yaml)
- [Primary Skill instructions](SKILL.md)

## Skill Output

默认一张 PNG/JPEG 成片。按请求增加对比 PNG、Prompt TXT 和对比元数据 JSON。
实际回读照片，检查身份、构图、光向、场景、缩略图与圆形裁切；不能靠工具成功代替验收。

## Skill Version

0.1.0

## Ethical Considerations

不自动公开照片、识别人名、持久化脸部信息或替换用户社交头像。保留素材权利与来源边界。
重构过的背景不能充当纪实证据。

## LovStudio Evidence

### User Cases

See [`cases/cases.json`](cases/cases.json). Every case must show Input → Prompt → Output.

真实雪山案例包含原照片角色、被否定的紧近景、黄衣参考、执行 Prompt、修正版引用和用户
确认。本次只核验分享页文字与引用，未重跑图像生成或重新检查照片像素。

### Dimension Map

机器卡列出身份/参考隔离、环境构图、对比真实性、复刻可追溯性四个维度及对应证据。
没有数值评测，分数均为 null；历史用户接受不能推广为模型保真度指标。

### Pricing Basis

See [`pricing-card.yaml`](pricing-card.yaml). Free Skills still explain their value,
boundary, and review trigger.

本地源包免费（¥0）；图像模型费用、人工服务及 Photoshop 许可不包含在内。
增加托管算力或人工服务时重新评估，不臆造调用成本。

### Distribution

Keep paid channels (`workbuddy`, `skillpay`) and free channels (`github`, `lovstudio`)
explicit. A planned or unavailable channel must not be described as live.

本地创建与安装；以上四个远程渠道均未发布。本次没有远程提交、上传或上架。
