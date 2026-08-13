---
name: lov-filing-monitor
description: >
  定期打开接入商、工信部或公安平台权威页面，比较备案状态并追加巡检台账；用户说“每天检查备案”“没变化就静默”或 "monitor the filing status" 时使用，只在变化或需人工动作时提醒。
license: MIT
metadata:
  author: LovStudio
  version: "0.1.0"
  card_standard: lovstudio/skill-card/v1
  tags:
    - filing-monitor
    - status-diff
    - audit-ledger
    - notification-policy
  compatibility: "Embedded module of lov-china-website-filing; scheduling and notification channels are supplied by the host."
  dependencies: []
---

# lov-filing-monitor — 备案状态巡检

## Input and output

- 输入：权威入口、巡检频率、台账路径、上一状态、静默/通知策略和完成门。
- 输出：本次权威状态、差异、用户动作、追加记录，以及按策略触发的通知或完成信号。

## Triggers

### Activate when

- 用户说“每天检查备案状态”“没变化就不要通知”“审核通过后暂停巡检”。
- User asks to "monitor the filing status" or "notify me only when the filing changes".

### Do not activate when

- 只需要一次性查询且不保留记录；直接使用对应 ICP 或公安模块。
- 用户要通用业务自动化而非备案状态机；交给宿主自动化或通用工作流能力。

## Workflow (MANDATORY)

1. 读取 `$KIT_DIR/references/status-taxonomy.md`、`authority-gates.md`、本模块组合记录和用户明确的通知策略。
2. 运行 `python3 "$KIT_DIR/scripts/filing_record.py" check --path RECORD`，读取上一条状态。
3. 复用用户当前已登录的浏览器会话，优先打开具体订单/申请详情，其次列表；搜索结果和旧记录不能充当当前状态。
4. 核验适用字段：域名实名同步、接入商审核、补充材料、短信核验、管局结果、DNS/HTTPS/页脚、公安审核与安全评估。
5. 先用 `compare` 判断权威来源、阶段、状态、域名状态和动作是否变化，再用 `append` 追加本次观察。
6. 无变化且无需用户动作时只写记录并静默。变化、登录/验证码阻塞、补充材料、驳回、通过或完成门满足时才按用户指定渠道通知。
7. 浏览器收尾时保留需要接管的 handoff 页面，清理本轮新开的无关标签页。

## Completion gate

监控只能在用户定义的最终权威门满足后暂停。ICP 中间状态、公安待审核、缓存备案号或无法登录都不能触发完成。

## Dependencies

Python 3.8+ for the ledger CLI. Scheduling, browser control and notifications are host-provided.
