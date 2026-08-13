---
name: lov-filing-readiness
description: >
  在提交中国大陆网站备案前核验主体、域名实名、服务类型、接入资源和材料缺口；用户说“备案前检查”“ICP 需要什么材料”或 "check ICP filing readiness" 时使用，并给出可执行准备清单。
license: MIT
metadata:
  author: LovStudio
  version: "0.1.0"
  card_standard: lovstudio/skill-card/v1
  tags:
    - icp-readiness
    - domain-real-name
    - filing-materials
  compatibility: "Embedded module of lov-china-website-filing; browser access is optional for live checks."
  dependencies: []
---

# lov-filing-readiness — 备案准备核验

## Input and output

- 输入：主办者、服务名称、域名、注册商、接入商/云资源、网站能力与目标地区。
- 输出：备案场景、已核验事实、材料清单、实名/资源缺口、专项许可风险和下一步。

## Triggers

### Activate when

- 用户说“备案前检查”“域名实名同步了吗”“ICP 需要什么材料”。
- User asks to "check ICP filing readiness" or "prepare a China website filing checklist".

### Do not activate when

- 已有订单并只需查看审核状态；使用 `lov-icp-filing` 或 `lov-filing-monitor`。
- 只需生成隐私政策、部署网站或购买域名，不属于备案准备核验。

## Workflow (MANDATORY)

1. 从 `$KIT_DIR/skill.yaml` 解析 Profile，敏感字段只在当前会话最小化使用；详见本模块的 `references/user-profile.md`。
2. 读取 `$KIT_DIR/references/official-rules.md`、`$KIT_DIR/references/authority-gates.md` 和本模块的 `references/skill-composition.md`。
3. 分类首次备案、新增服务、接入、变更或注销；识别网站、APP、小程序或仅 API。
4. 核验域名实名所有者、证件类型/有效期、域名后缀、接入资源资格、服务器地域和主体所在地要求。
5. 盘点主体证件、负责人信息、域名证明、真实性核验及可能的前置审批；不把接入商通用清单写成当地最终要求。
6. 检查论坛、评论、群组、直播、信息分享、算法、生成式 AI、新闻/出版/教育/医疗等能力，只标记可能的专项义务，不自行作法律结论。
7. 输出 `ready`、`ready-with-risks` 或 `blocked`，每项标注 `verified`、`user-stated`、`inferred` 或 `unknown`。

## Completion gate

只有备案类型、主体/域名匹配、接入资源和必需材料都有可追溯依据时才可称 `ready`。准备就绪不等于已提交或已通过。

## Dependencies

None for offline planning. Live verification requires the relevant registrar and provider pages.
