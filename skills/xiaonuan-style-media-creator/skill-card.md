# 晓暖说媒风格短视频 · Xiaonuan Matchmaker Style Video · Skill Card

## Description

依据带时间证据的八维风格协议，把连麦录像或新选题做成剪辑计划，并用内置模板渲染直播连麦切片的包装与封面，同时检查事实、结构与授权边界。

## Owner

本地 Skill 维护者与 contributors；不代表参考作者授权、合作或背书，未创建公开支持渠道。

## License

代码、原创协议与模板采用 MIT。原片、人像、声音、台词、截图、封面与品牌标识的权利不转授，包内不含这些素材。

## Use Case

参考作品到风格包；自己的连麦录像或新选题到剪辑计划、渲染数据、切片成片与 3:4 封面。不是婚恋或职业咨询服务，也不负责发布。

## Deployment Geography

Local-first，在兼容 Skills 的本地 AI 宿主中使用。

## Requirements

生成由宿主 AI 执行，不要求固定云账号。校验需 Python、jsonschema、PyYAML；出片需 FFmpeg、numpy、Node.js 与 Remotion 4.0.517；重分析另需 OpenCV、Pillow、librosa、swiftc 与带时间戳的 ASR。凭据不进入包。

## Known Risks

可能被用来冒充原作者、挪用她的品牌，或把原作里的市场判断和刻板说法当事实；也可能公开真实来访者的敏感信息。以不含原素材、品牌禁用清单、来访者同意记录、事实台账与状态分级缓解。

## References

[入口](SKILL.md)、[风格 JSON](assets/xiaonuan-v0.1/style-profile.json)、[证据](assets/xiaonuan-v0.1/evidence.jsonl)、[留出报告](assets/xiaonuan-v0.1/holdout-report.json)、[模板](templates/remotion/README.md)。

## Skill Output

风格协议 JSON/JSONL、剪辑计划、渲染数据、单一连续音轨、MP4 切片、3:4 封面与审阅 JSON。剪辑计划不等于已渲染，已渲染不等于已发布。

## Skill Version

0.1.0，2026-11-08。

## Ethical Considerations

不冒充作者，不复用她的素材与品牌，不捏造来访者、资质或亲历，不把刻板印象与市场臆断当事实，未经同意不公开来访者信息，不自动发布。

## User Cases

真实 12 条来源：10 条训练、2 条留出，全文转写、全片测量、每 2 秒一帧 OCR。另有用《易七猫对话手工川》素材重剪的 72.5 秒演示：5 段、48 条字幕，计划校验通过并已渲染，响度 -15.7 LUFS、峰值 -4.4 dBTP；重剪版发布同意未确认。

## Dimension Map

证据可追溯：219 条证据与支持样本可重算。
计划可执行：剪辑计划可校验并转成渲染数据，模板复现演示画面。
留出与例外：留出 48 项检查命中 37，未中项与 v0.2 候选保留。
出片质检：响度、峰值、提示音、黑场静音与重转写剪口有记录。
四项都不伪造人工评分；自动通过不是人类偏好认可。

## Pricing Basis

本地 Skill 免费；外部模型、ASR、拍摄、来访者授权、字体授权、渲染与发布不包含。变更服务范围时重新评估，不暗示已有付费发行。

## Distribution

LovStudio 官网目录：免费条目（0 Credits），公开副本为 lovstudio/skills 中的目录镜像。源码托管在 lovstudio 组织的私有仓库，仅供维护。WorkBuddy、SkillPay 未发布。
