# YOLO 模式 · YOLO Mode · Skill Card

## Description
当前 session 必要权限的预检与配置，以及当前任务的非交互执行。只使用宿主正式允许的接口，配置后回读；受阻步骤延期并继续独立工作。

## Owner
本地 Skill 维护者；通过本地源码变更记录联系，未建立公开支持渠道。

## License
MIT，见 LICENSE；不包含第三方服务额度。

## Use Case
离开电脑前显式启用，输入当前目标、预设与授权范围，获得原任务产物和恢复记录。

## Deployment Geography
全球；支持 Agent Skills 的本地宿主，实际能力受宿主约束。

## Requirements
核心为指令型。Python 3.8+ 用于 Profile，PyYAML 用于校验。
依赖 lov-branding-consistency 审校最终可见说明；业务连接需已有授权。

## Known Risks
宿主审批会暂停、系统休眠会中断；预检与检查点降低损失，不提供后台存活保证。
不得将自主决策当作无限授权；未知远端结果先回读，避免重复副作用。

## References
[执行合同](SKILL.md)、[能力组合](references/skill-composition.md)、[非交互预检](references/noninteractive.md)。

## Skill Output
原任务产物、验证证据、状态与恢复记录。关键事实缺失或权限不足时保留延期条件。

## Skill Version
0.2.0

## Ethical Considerations
不替用户批准、不扩大外部操作范围、不保存秘密；用户取消与宿主限制优先。

## User Cases
[真实创建请求与产出](cases/cases.json)。当前真实案例是 Skill 的创建与本地安装，
不是整夜运行成功案例；人工行为演练见 cases/behavior-review.md。

## Dimension Map
非交互决策、授权边界、恢复与真实性、Session 权限准备四个维度的证据列于 skill-card.yaml。
分数均未评定，没有足够跨宿主样本支持量化遵循率。

## Pricing Basis
免费本地使用。无自营云端运行服务；模型、宿主与外部工具成本按用户现有服务计。
引入托管服务或维护成本变化时复评，不自动收费。

## Distribution
本地安装；GitHub、LovStudio、WorkBuddy、SkillPay 均未发布。没有付费发行渠道。
