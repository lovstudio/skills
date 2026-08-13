---
name: lov-domain-cutover
description: >
  在 ICP 通过后把备案域名安全切换到中国大陆网站，核验部署、DNS、证书、HTTPS、ICP 页脚和旧域名处理；用户说“备案通过后绑定域名”或 "cut over the filed domain" 时使用。
license: MIT
metadata:
  author: LovStudio
  version: "0.1.0"
  card_standard: lovstudio/skill-card/v1
  tags:
    - domain-cutover
    - dns
    - tls
    - icp-footer
  compatibility: "Embedded module of lov-china-website-filing; provider-specific tools are selected at runtime."
  dependencies: []
---

# lov-domain-cutover — 备案后域名上线

## Input and output

- 输入：ICP 通过证据与服务备案号、目标域名、部署服务、DNS/证书现状和旧域名策略。
- 输出：可访问的 HTTPS 域名、ICP备案展示、旧域名结果和真实回读证据。

## Triggers

### Activate when

- 用户说“备案通过了，部署并绑定域名”“把新域名替换旧域名”“网站底部加 ICP 号”。
- User asks to "cut over the filed domain" or "verify DNS, TLS, and the ICP footer".

### Do not activate when

- ICP 尚未通过或服务备案号无法权威回读；不得开放中国大陆网站，返回上游。
- 只做通用构建、不涉及备案域名开放；使用生产构建或部署能力。

## Workflow (MANDATORY)

1. 读取 `$KIT_DIR/references/status-taxonomy.md`、`authority-gates.md` 和本模块组合记录。
2. 重新核验 ICP 通过、备案号、域名和目标接入资源的对应关系。
3. 先验证可部署制品和服务健康，再申请/绑定证书并配置 DNS；不要用浏览器缓存代替 DNS/TLS/HTTP 检查。
4. 仅在用户明确授权时解绑、替换或使旧域名失效。保留可回滚路径，避免误删 DNS 区域或证书。
5. 在首页底部展示准确服务备案号并链接 `https://beian.miit.gov.cn/`；按当前管局/接入商要求核验根域与 `www`。
6. 从外部真实访问域名，检查解析、证书主机名、HTTP 状态、预期页面、备案号文字与链接。
7. 输出 `completed` 或 `partially-verified`，并向公安备案模块交接网站开通时间、域名、IP/接入商和公开页脚证据。

## Completion gate

控制台显示“绑定成功”不够；DNS、TLS、页面内容和 ICP 页脚必须从真实域名回读。旧域名结果必须与用户授权一致。

## Dependencies

The site's existing deployment, DNS and certificate providers; no provider is hard-coded.
