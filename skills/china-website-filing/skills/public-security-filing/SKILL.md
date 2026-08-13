---
name: lov-public-security-filing
description: >
  协助已取得 ICP 并开放的网站办理公安联网备案，核验主体账号、网站与接入信息、材料、属地审核和公安备案号，并分流舆论属性安全评估；触发词包括“公安备案”与 "public security filing"。
license: MIT
metadata:
  author: LovStudio
  version: "0.1.0"
  card_standard: lovstudio/skill-card/v1
  tags:
    - public-security-filing
    - mps
    - security-assessment
    - compliance-footer
  compatibility: "Embedded module of lov-china-website-filing; live operations require an authenticated public security platform session."
  dependencies: []
---

# lov-public-security-filing — 公安联网备案

## Input and output

- 输入：ICP 通过证据、网站开通时间、主体/负责人、域名、服务器/IP、接入商/注册商、网站能力与材料。
- 输出：公安申请草稿/提交状态、审核单位、补充动作、公安备案号、页脚代码与安全评估分支状态。

## Triggers

### Activate when

- 用户说“继续公安备案”“企业能用个人账号办理吗”“这个网站公安备案怎么填”。
- User asks to "submit a public security filing" or "add the MPS filing number to the website".

### Do not activate when

- ICP 尚未通过或网站未在中国大陆公网开放；先完成上游阶段。
- 用户只问一般网络安全加固、等保测评或刑事法律问题；不属于公安联网备案表单流程。

## Workflow (MANDATORY)

1. 读取 `$KIT_DIR/references/official-rules.md`、`authority-gates.md`、`status-taxonomy.md` 和本模块组合记录。
2. 核验 ICP 号、真实可访问网站、开通时间与三十日基线；运行时以属地公安和平台提示为准。
3. 优先使用与申报主体一致的法人/单位账号。平台明确允许特殊情况下用个人账号办理企业备案时，仍保持企业为申报主体，不混淆账号持有人与网站开办者。
4. 填写开办主体、负责人、网站、域名注册商、网络接入商、服务器/IP、服务类型与功能；不猜证件、电话、地址或业务能力。
5. 对论坛、评论、群组、直播、信息分享、小程序、算法或生成式 AI 等能力逐项按真实产品判断。平台提示安全评估时，创建独立状态并在提交前请求明确授权。
6. 上传用户指定材料并保存草稿。责任书、验证码和最终提交按门控交还用户；授权后执行并回读申请时间、状态和审核单位。
7. 审核通过后复制平台提供的备案号、链接、HTML 和图标，更新网站并真实回读；未通过前不得伪造占位号。

## Completion gate

“已提交/待审核”不是完成。必须有公安权威页面通过、网站对应备案号，以及按平台代码上线的页脚回读。安全评估若适用，单独验收。

## Dependencies

Authenticated access to the National Internet Security Management Service Platform or the competent local authority.
