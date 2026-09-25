# Skill 命名大师 · Skill Naming Master · Skill Card

## Description

为单个或整组 Skill 选择准确、简短、优雅、一致的中英文名称。保留用户认可原文，
用真实能力支撑命名，并交付可回读的逐项清单。

## Owner

LovStudio；通过本地源码维护者反馈。

## License / Terms

MIT，见 [LICENSE](LICENSE)。示例名称不构成商标授权或可注册性声明。

## Use Case

面向 Skill 创作者与目录维护者。输入能力资料、旧名称、稳定标识与风格范例；
适用于新 Skill 起名、单项改名和整组风格审查。

## Deployment Geography

全球；支持 Agent Skills 的本地或云端宿主。

## Requirements / Dependencies

品牌门禁依赖 lov-branding-consistency；核心判断使用宿主语言能力。
离线审计与 Profile 使用 Python 3.8+ 标准库，源码校验另需 PyYAML，无凭据要求。

## Known Risks and Mitigations

产品化表达可能夸大范围，需核对实际输入与输出。批量改名可能误改认可拼写或调用
标识，需锁定认可值并分离显示名。结构通过不代表审美优秀或已经发布。

## References

- [执行合同](SKILL.md)
- [命名判断](references/naming-style.md)
- [真实案例](cases/cases.json)
- [机器可读卡片](skill-card.yaml)

## Skill Output

单个请求给最佳名称与简短理由；批量结果为 Markdown 表格及 JSON 命名清单。
参数包括能力证据、旧名、风格、认可值、语言与范围。验收覆盖能力准确性、重复名称、
认可原文、完整覆盖和品牌语境。

## Skill Version

0.1.0

## Ethical Considerations

不上传私有能力资料，不伪造认可、商标可用性或审美分数。命名建议不授予修改调用
标识、发布或下架权限。

## LovStudio Evidence

### User Cases

历史批量任务留下 156 项目录名称，其中 138 项中文改变；本次将其作为真实结果回放，
并完成新 Skill 自身命名。历史发布与当前执行分开记录，见 [案例来源](cases/evidence/provenance.md)。

### Dimension Map

| 维度 | 证据 | 分数状态 |
| --- | --- | --- |
| 准确 | 自身命名与 GitHub 仓库简介命名决策 | 未量化 |
| 简短 | 156 项新旧名称对照 | 未进行记忆测试 |
| 优雅 | 用户认可范例与中英文编辑判断 | 无独立审美评分 |
| 一致 | 认可值与重复名称的结构审计 | 结构检查，不替代语义评估 |

### Pricing Basis

当前免费，含命名方法、案例与离线审计。模型费用、商标检索、人工咨询和代发布不在
交付范围内。加入托管或专业人工服务后复评，见 [定价说明](pricing-card.yaml)。

### Distribution

| 渠道 | 当前状态 |
| --- | --- |
| workbuddy | 未发布 |
| skillpay | 未发布 |
| github | 未发布 |
| lovstudio | 未发布 |

当前仅交付并验证本地源码与安装。
