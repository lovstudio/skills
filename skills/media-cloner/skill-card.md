# 视频风格复刻 · Video Style Cloner · Skill Card

## Description

从任一博主的公开作品得到一份冻结的、带时间证据的八维风格包，附留出检验、风格说明书与参数化包装模板；用户要求时，可再封装成该博主的专属风格 Skill。

## Owner

本地 Skill 维护者与 contributors。被分析的博主与本 Skill 没有合作、授权或背书关系。未创建公开支持渠道。

## License

代码、协议、Schema 与模板采用 MIT。被分析作品的原片、人像、声音、台词、截图、封面与品牌标识的权利不因分析而转授，包内不含这些素材。

## Use Case

输入是博主主页或作品链接。输出包括：

- 冻结样本清单；
- 只留在本地的测量与转写；
- 风格包（画像、证据、冻结记录、留出报告）；
- 风格说明书、模板参数与预览。

可选产物：用用户自己的素材做的演示，以及专属风格 Skill。本 Skill 不负责下载、登录与发布。

## Deployment Geography

Local-first，在兼容 Skills 的本地 AI 宿主中使用。

## Requirements

| 用途 | 依赖 |
| --- | --- |
| 台账与校验 | Python 3.9+、jsonschema、PyYAML |
| 测量 | FFmpeg/FFprobe、numpy、OpenCV、Pillow |
| OCR | macOS Vision（swiftc 编译） |
| 本地转写 | mlx-whisper 或 openai-whisper；也可导入 Whisper、听悟或 SRT 转写 |
| 模板 | Node.js 与 Remotion 4.0.517 |

需要登录的平台由用户自己的浏览器会话读取，凭据不进入包。

## Known Risks

可能出现的问题：

- 冒充博主或挪用其素材与品牌；
- 规则过拟合到爆款；
- 把原作观点当事实迁移；
- 把自动校验当风格认可；
- 访问平台时越权。

对应的缓解措施：

- 风格包只记手法，原始素材只留在本地；
- 分层选样，冻结拆分，冻结后逐条做留出检验并单列受污染项；
- 遵守作者性契约，状态分级；
- 只读公开作品，不替用户登录。

## References

- [入口](SKILL.md)
- [分析协议](references/analysis-protocol.md)
- [规则与证据](references/rules-and-evidence.md)
- [模板与演示](references/template-and-demo.md)
- [封装](references/packaging.md)
- [复现报告](cases/regression-xiaonuan/report.json)

## Skill Output

- 样本清单与冻结拆分；
- 风格包：style-profile.json、evidence.jsonl、FROZEN.json、holdout-report.json；
- 风格说明书（Markdown）；
- 模板参数与 PNG 预览；
- 可选：MP4 演示。

风格包通过校验不等于风格认可；渲染完成不等于已发布。

## Skill Version

0.1.0，2026-11-09。

## Ethical Considerations

- 不冒充被分析的博主，不复用其素材、头像、声音与品牌。
- 不绕过平台访问限制，不收集评论区个人信息。
- 不把原作观点和刻板说法当事实迁移。
- 演示只用用户自己的素材，并取得出镜者同意。
- 不自动发布。

## User Cases

**晓暖（清醒择偶）说媒（2026-11-08，小红书）。**

- 样本：从当前格式期分层抽 12 条，分析前冻结 10/2 拆分。
- 风格包：32 条规则、219 条证据。
- 留出检验：记录 48 项，命中 37。
- 后续：封装为 `lov-xiaonuan-style-media-creator`，已上线官网。

这次的手工流程就是本 Skill 的来源。

**老张心理（小红书）。**

- 样本：10 条，8/2 拆分。
- 风格包：23 条规则、157 条证据。
- 后续：封装为 `lov-laozhang-style-media-creator`。

**内部复现。** 用本 Skill 的工具在晓暖原始数据上重建 v0.1 冻结包，结果如下：

- 画像与证据文件逐字节一致；
- 测量、OCR、提示音与训练集分布均与原值一致；
- 模板填入晓暖参数后与专用模板逐像素一致。

同一工具复查发现，晓暖的留出报告只覆盖了 64 个“规则 × 样本”组合中的 48 个，其中 11 项受污染。

本 Skill 还没有独立完成过新博主的端到端案例。

## Dimension Map

- **证据可追溯**：引文逐字可查，数字可回读，支持数由证据推出。
- **留出纪律**：冻结前由工具封存留出样本，冻结后要求逐条覆盖。
- **可复现**：在晓暖数据上逐字节复现 v0.1。
- **出片衔接**：模板逐像素复现，音轨复现响度与对齐。

四项都没有人工评分，自动通过不代表人类偏好认可。

## Pricing Basis

LovStudio 官网目录免费条目（0 Credits），本地使用同样免费。证据来自在晓暖原始数据上的内部复现，还没有新博主的端到端案例，所以先用免费入口积累使用证据。外部 ASR、下载、拍摄、授权、字体、渲染与发布费用不包含。第一个新博主端到端案例完成、累计 10 次外部完整使用、人工风格评审，或交付范围、依赖、支持成本变化时，由 `lov-skill-pricing` 复评。

## Distribution

LovStudio 官网目录：免费条目（0 Credits），公开副本为 lovstudio/skills 中的目录镜像。源码托管在 lovstudio 组织的私有仓库，仅供维护。WorkBuddy、SkillPay 都没有发布，也没有收到发布请求。本地已安装。
