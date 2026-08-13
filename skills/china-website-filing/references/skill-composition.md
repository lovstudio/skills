# Skill Group Composition

## Nearby Skills Inspected

| Skill | Classification | Routing contract and decision |
| --- | --- | --- |
| `lov-fill-web-form` | optional upstream atom | 从网页字段和知识库生成预填 Markdown；不拥有权威页面状态、备案阶段门或最终提交，因此只可提供字段草稿。 |
| `lov-fact-check` | optional upstream atom | 适合核验当前法规或地方口径；本 Kit 仍自行保存备案专用的一手来源、状态词表与完成门，实时检索结果以制品级摘要交接。 |
| `lov-dev-to-prod` | optional upstream/downstream atom | 拥有通用生产构建与本地制品验证；不拥有 ICP 审核、DNS 开放时机或备案页脚。若网站尚未具备可部署制品，可先生成生产制品再交回本 Kit。 |
| `lov-legal-pages` | adjacent, not composed | 生成隐私政策和服务条款页面，不办理备案，也不决定公安安全评估适用性。 |
| `automation-workflows` | optional downstream atom | 能设计通用定时工作流；备案巡检的权威状态比较和静默/通知策略由内嵌 `filing-monitor` 模块拥有，宿主调度可作为外部触发器。 |

已搜索本地 Skill 源与安装目录，没有发现一个同时拥有 ICP、备案后域名切换、公安联网备案和权威状态巡检的现有 Skill。

## Atomic Handoffs

```text
optional: lov-fact-check
  dated official-rule evidence
              |
              v
lov-china-website-filing
  readiness -> ICP -> cutover -> public security -> monitor
              |
              +--> optional lov-dev-to-prod
              |    production web artifact
              |
              +--> optional host automation
                   scheduled trigger only
```

每个交接必须包含具体制品：事实核验交付带日期和链接的规则摘要；生产能力交付可部署制品与验证结果；调度器只触发巡检，不拥有状态解释。

## Overlap Decisions

- 网页填表只复用“字段草稿”概念，不复制深度知识库检索或通用表单输出格式。
- 法规核验遵循一手来源原则，但本 Kit 内保留最小运行规则，避免把外部 Skill 变成硬依赖。
- 域名切换只覆盖“ICP备案后的大陆站点开放与备案展示”，不复制通用应用生产构建或发布全流程。
- 巡检模块内嵌，因为它必须理解 ICP、域名、公安和安全评估的状态关系；调度实现由宿主决定。

## Composition Decision

选择 **self-contained Skill Kit**。五个阶段都可独立产生有价值结果，但完整上线必须共享同一主体/域名证据、严格顺序和完成门。把它们拆成外部依赖会丢失状态一致性；把它们压成一个单体流程又会阻碍用户从中间阶段恢复。
