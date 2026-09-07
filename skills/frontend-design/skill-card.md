# 界面设计师 · Interface Designer · Skill Card

## Description

手工川工作室维护的通用前端设计 Skill。把需求、真实内容和现有代码落实为有辨识度、
交互一致、支持图片音视频的界面；风格由目标内容与项目约束决定。

## Owner

LovStudio contributors；维护入口为 Skill 真源仓库。

## License / Terms

[MIT](LICENSE) 适用于本包指令与配套工具，保留来源归属。案例作品和第三方素材不随
本包重新授权。旧版来源说明见 [Provenance](references/provenance.md)。

## Use Case

面向产品开发者、设计者和代码 Agent。输入为需求、真实素材、现有页面或项目，输出
为可运行界面或只读审查。适用页面、工具栏、设置、导航与多媒体教学展示。

## Deployment Geography

全球本地 Agent 与项目环境；作品可按任务部署在用户自己的环境。

## Requirements / Dependencies

文案门禁依赖 `lov-branding-consistency`。复用项目工具链，运行验收需要浏览器能力；
Profile 与 Skill 校验需要 Python 3.8+ 和 PyYAML。核心方法不需要凭据，发布另按任务授权。

## Known Risks and Mitigations

- 新视觉破坏旧习惯：先读取相邻控件、token 和用户路径。
- 资源存在被当成媒体可用：实际播放、拖动、点击和触控分别记录。
- 私人素材泄露：区分公开范围，记录来源，不携带聊天原件、秘密或私人路径。
- 历史成果夸大新能力：历史案例与新版演练分别归档，不使用无依据评分。

## References

- [主入口](SKILL.md)
- [验收方法](references/acceptance.md)
- [机器卡片](skill-card.yaml)
- [来源说明](references/provenance.md)

## Skill Output

项目原生前端源码、明确的内容层级与控件状态、真实素材引用和可追溯验收。
只读审查输出核实的问题、影响和检查边界。发布不作为默认副作用。

## Skill Version

0.3.0。由本地通用名 frontend-design 0.2.0 的工作室方法整理而来，新包独立命名和安装。

## Ethical Considerations

不虚构案例、来源、用户评价或量化评分。品牌来自当前任务和 Profile，不以维护者
品牌覆盖其他用户。保留真实或合成媒体标识，不把构建通过声称为全部体验已验证。

## User Cases

[cases/cases.json](cases/cases.json) 保存真实 Input → Prompt → Output：
能力地图多媒体展示、官网资源入口，以及单独标识的新版本只读演练。
前两项早于本 Skill 创建，归档运行证据不代表 0.3.0 重新创造了这些作品。

## Dimension Map

| 维度 | 证据 | 当前状态 |
| --- | --- | --- |
| 产品交互 | 桌面、手机菜单到达真实地图 | 新演练入口已验；窄屏菜单另有待修问题 |
| 内容表达 | 244 节点、6 案例与可检索索引 | 历史案例已验 |
| 多媒体 | 图片、两段声音、视频播放与跳转 | 历史案例已验 |
| 可移植性 | Profile、相邻能力边界和独立 ID | 契约审查 |
| 动效与可访问性 | 减少动效、清理、键盘与文本路径规则 | 规范已写，完整运行覆盖未完成 |

这些状态表示证据成熟程度，不是能力百分比或综合分数。

只读演练发现 320×740 视口下，长菜单底部的登录入口未完整露出，菜单滚轮也未使它
完整可见。能力地图入口本身可触控跳转；本次没有修改网站。见
[窄屏问题记录](cases/evidence/narrow-menu-finding.json)。

## Pricing Basis

免费提供本地指令与案例，模型、媒体制作和部署费用另计。
[pricing-card.yaml](pricing-card.yaml) 保留源码开放使用依据；官网发行定价卡在 Publisher
输出与目录中维护，产品展示使用 Credits。

## Distribution

渠道状态由 Publisher 在源码之外维护，以
[官网目录](https://lovstudio.ai/skills/frontend-design) 和对应 Release 为准。
案例网页上线与 Skill 上架是两个状态。
