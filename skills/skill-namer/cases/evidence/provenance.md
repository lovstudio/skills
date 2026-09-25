# 案例来源与边界

日期：2026-09-07。源自用户在本地创建、迁移与统一命名 Skill 的真实任务。
历史结果用于方法沉淀和回归，不能当作新 Skill 独立完成过整组发布的证明。

## 历史输入与认可基准

用户原话：“所有 skills 的命名都应该尽可能准确、简短、优雅、一致”。
随后要求“所有的 skills 都应该参考这种风格集体更新同步”。
风格来自用户指定的历史任务
[下架 SkillPay 其余全部 Skill](codex://threads/01a07b41-48e6-7de3-8de2-f2df01a9b4d5)，
其中的下架行为不是本 Skill 的命名权限。

| 稳定标识 | 用户认可的中文名 |
| --- | --- |
| wdb-cli | 万能微信秘钥 |
| hanzi-lens | 汉字镜 |
| wxmp-cracker | 公众号神器 |
| bp-deck | BP 大师 |
| any2pdf | PDF大师 |
| any2deck | PPT 大师 |
| write-professional-book | 写书专家 |
| event-poster | 专业海报 |
| professional-infographic | 专业信息图 |
| subtitle-freedom | 人人字幕 |
| oh-my-landingpage | 官网小能手 |
| better-github-desc | GitHub 仓库简介优化 |

最后一项来自当前任务中用户的明确选择：“个人觉得「GitHub 仓库简介优化」可以的”。
只将这些中文值标为用户认可；其他中文调整和英文名称是编辑建议，不扩大认可范围。

## 历史结果与本次回放

原任务审查 251 份本地来源；官网目录 156 项中，138 项中文名称改变。
本包保存公开目录的新旧名称与能力简介摘录，不包含付费执行源码或私有 Profile。
原字段不存在时 before 保留空字符串，不猜一个旧名。

- [历史统计](historical-result.json)：历史任务已记录的结果，不是本次重新在线验证。
- [能力摘录](catalog-capabilities.json)：原目录中的 description 和 tagline。
- [命名清单](catalog-review.json)：156 项，一项不漏，保留 12 个中文认可值。
- [回放结果](catalog-audit.json)：本 Skill 的只读结构检查；中英文任一变化算 rename，
  因此与仅统计中文变更的 138 项口径不同。

历史公开记录：[命名更新 PR](https://github.com/lovstudio/skills/pull/42)、
[同步修复 PR](https://github.com/lovstudio/skills/pull/43)。本次未重新执行其发布流程。
历史案例保留当时名称，不随未来目录变更自动重写。

## 当前自身命名

当前用户请求：“基于此，应该再创一个 skill 命名大师”。
输出“Skill 命名大师”，英文为编辑建议“Skill Naming Master”，调用标识
`lov-skill-namer`。能力限定为 Skill 命名，避免与通用项目起名混淆。

按新工作流核对：实际输出是名称与命名清单；“Skill”限定对象，“命名大师”保留
用户的角色表达；英文自然对应；作者信息不进入名称。与 Skill 工坊、Skill 精修师、
Skill 发布助手的职责区分可在能力组合表回读。

[自身清单](self-naming-review.json) 和 [结构结果](self-naming-audit.json) 是本次实际执行。
[验证记录](validation.json) 分开记录机械验证和人工合同走查；没有虚构独立用户评分。
