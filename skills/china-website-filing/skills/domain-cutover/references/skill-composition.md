# Skill Group Composition

## Nearby Skills Inspected

| Skill or module | Classification | Decision |
| --- | --- | --- |
| `lov-china-website-filing` | owning Kit | 提供共享 Profile、权威规则、提交门、状态词表和统一台账。 |
| `lov-dev-to-prod` | optional external atom | 只接受明确的制品级交接，不作为隐藏依赖。 |
| Kit sibling modules | upstream/downstream atoms | 通过域名、阶段状态、证据时间和下一动作交接。 |

## Atomic Handoffs

- 上游：icp-filing 的权威通过证据；可选 lov-dev-to-prod 的可部署网站制品
- 本模块：备案后域名上线。
- 下游：将网站开通时间、域名、IP/接入商与页脚证据交给 public-security-filing

## Overlap Decisions

只拥有备案后的大陆域名开放与合规展示，不复制通用生产构建或完整发布流程。

## Composition Decision

本模块是 `lov-china-website-filing` 的**内嵌原子模块**。它可单独调用，但跨阶段时依赖 Kit 内共享的证据和完成门；不拆成外部安装依赖。

