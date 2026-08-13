---
name: lov-icp-filing
description: >
  协助提交和跟进中国大陆网站 ICP 备案，覆盖接入商审核、域名实名同步、补充材料、工信部短信核验和管局结果；用户说“继续 ICP 备案”或 "submit and track an ICP filing" 时使用。
license: MIT
metadata:
  author: LovStudio
  version: "0.1.0"
  card_standard: lovstudio/skill-card/v1
  tags:
    - icp-filing
    - provider-review
    - sms-verification
    - authority-review
  compatibility: "Embedded module of lov-china-website-filing; live operations require an authenticated provider session."
  dependencies: []
---

# lov-icp-filing — ICP 申请与审核

## Input and output

- 输入：准备核验结果、备案场景、接入商订单、主体/服务/域名和材料。
- 输出：提交/审核状态、实名同步状态、补充材料、短信核验动作、管局结果和服务备案号。

## Triggers

### Activate when

- 用户说“继续 ICP 备案”“提交备案订单”“工信部短信怎么核验”“管局审核到哪了”。
- User asks to "submit and track an ICP filing" or "check the authority review status".

### Do not activate when

- 用户只有备案想法但未准备主体、域名或接入资源；先用 `lov-filing-readiness`。
- ICP 已通过且只需上线或办公安备案；分别使用后续模块。

## Workflow (MANDATORY)

1. 读取 `$KIT_DIR/references/official-rules.md`、`authority-gates.md`、`status-taxonomy.md` 和本模块组合记录。
2. 打开具体接入商订单详情或备案订单列表；只有当前已登录的权威页面能作为最新状态。
3. 核验主体、服务、域名、备案类型、域名实名同步、接入资源和材料清单；把页面原文与 Agent 解释分开。
4. 在明确授权范围内填表和上传材料。遇到登录、验证码、扫码、人脸、真实性承诺或最终提交时停下交还用户。
5. 接入商审核后检查是否需要补充材料。提交管局后检查工信部短信核验及实际截止时间，提醒用户自行完成验证码。
6. 管局审核期间只追加状态。只有权威页面明确通过且服务备案号可回读时标记 `approved`。
7. 将观察追加到统一台账，并向 `domain-cutover` 交接备案号、域名、接入资源和证据时间。

## Completion gate

“短信核验完成”“已提交管局”或“管局审核中”都不是 ICP 完成。必须有审核通过和对应服务备案号。

## Dependencies

Authenticated provider session for live operations; user-owned phone/SMS verification when requested by MIIT.
