# 老张心理风格短视频 · Skill Card

## Description

依据带原片时间证据的八维风格协议，为新选题生成原创口播、分镜和制作计划，并检查事实与结构边界。

## Owner

本地Skill维护者与contributors；不代表参考作者授权、合作或背书，未创建公开支持渠道。

## License

代码与原创协议MIT。原片、人物、台词、截图和音乐权利不转授；附图为本地分析证据，不默认用于新片发布。

## Use Case

已授权参考作品到风格包；新选题与事实到脚本、字幕、分镜和连续时间线。不是默认成片、医疗诊断或发布服务。

## Deployment Geography

Local-first，在兼容Skills的本地AI宿主中使用。

## Requirements

日常生成由宿主AI执行，不要求固定云账号。校验需Python、jsonschema、PyYAML；重新测量另需FFmpeg、OpenCV、numpy、Pillow，可选macOS Vision。凭据不进入包。

## Known Risks

模型可能把动机推断当事实、把抽样当全片、把相似文风当身份授权。以来源证据、适用条件、未知、权利检查与人工确认缓解，不编造相似度或疗效。

## References

[入口](SKILL.md)、[风格JSON](assets/laozhang-v0.1/style-profile.json)、[证据](assets/laozhang-v0.1/evidence.jsonl)、[留出报告](assets/laozhang-v0.1/holdout-report.json)。

## Skill Output

风格协议JSON/JSONL、口播Markdown、事实台账、分镜、edit-plan与审阅JSON。制作计划不等于已拍摄/已渲染成片。

## Skill Version

0.1.0，2026-10-24。

## Ethical Considerations

不冒充作者、不默认复制声纹/人脸、不捏造资质或亲历，不将来源中的心理分析当临床事实，不自动发布。

## User Cases

真实10条来源：8条训练与2条留出，全文转写、全片测量及120帧证据。另有实际生成的96秒新题案例，619文本单位、8段、58条字幕；情境为虚构演示，未拍摄/渲染。

## Dimension Map

证据可追溯：157条证据与支持样本可重算。
计划可执行：Schema、时间线、字幕与事实引用可运行验证。
泛化边界：留出报告保留时长/切换密度/结尾等例外。
三项不伪造人工评分；自动通过不是人类偏好认可。

## Pricing Basis

本地Skill免费；云模型、ASR、拍摄、配音、音乐授权、制作与发布不包含。变更商业服务范围时重新评估，不暗示已有付费发行。

## Distribution

本次仅本地封装与安装。GitHub、LovStudio、WorkBuddy、SkillPay均未发布；未创建远端仓库或上传内容。
