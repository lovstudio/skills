# Skill Group Composition

## Nearby Skills Inspected

- `automation-workflows`：面向 Zapier、Make、n8n 的通用流程设计，适合评估业务自动化机会；不拥有 Yoda 原生记录、时区回读或运行证据。
- `feishu-cron-reminder`：将固定消息投递到飞书会话；它拥有飞书路由和主会话约束，不拥有 Yoda 自动化生命周期。
- `lov-filing-monitor`：嵌入式备案领域巡检模块，拥有权威状态比较与静默策略；其调度和通知由宿主提供。

## Atomic Handoffs

- 上游：`automation-workflows` 可交付频率、条件、动作和错误处理的流程 brief；本 Skill 把 brief 转为 Yoda 原生计划并以保存后的自动化记录为验收物。
- 下游：`feishu-cron-reminder` 可消费已确认的提醒文本与频率，在用户明确选择飞书时投递；飞书消息送达由该 Skill 验收。
- 下游：领域监控 Skill 可交付状态差异、完成门和通知策略；本 Skill 负责其 Yoda 计划与运行证据。

## Overlap Decisions

本 Skill 不重复构建第三方自动化平台流程，也不承担飞书消息路由。它专门处理 Yoda 的 schedule contract、记录修复、去重、运行回读与停用。

## Composition Decision

选择 Single Skill。计划设计、配置、验证和停用共享同一条 Yoda 自动化记录与同一验收边界，拆为 Kit 模块会增加交接而不增加独立用户价值。外部能力均为可选、工件级交接。
