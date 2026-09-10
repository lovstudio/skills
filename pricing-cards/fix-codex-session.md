# Skill Pricing Card：fix-codex-session

| 项目 | 结论 |
| --- | --- |
| 版本 / 交付单元 | 0.2.0 / 公开 Skill 源码、两个可复验的本地 CLI（rollout 诊断与修复副本、provider 绑定同步）、故障手册与可信度卡 |
| 目标买家 | 线程卡在 tool-call 校验错误、或切换 provider / 中转站后旧线程打不开的 Codex Desktop / CLI 用户 |
| 建议价格 | 0 Credits |
| 稳定价格带 | 0 Credits，保持公开免费入口 |
| 首发测试价 | 0 Credits，持续到出现外部真实使用与长期维护需求 |
| 渠道 | LovStudio 官网 Skill Publisher |
| 置信度 | case-backed；两个真实恢复案例与实跑输出已记录，外部使用样本仍然有限 |

## 为什么是免费

- 成本底线：约 6–10 小时需求排查、实现、文档与验证（0.1.0 诊断与修复副本，0.2.0 provider 同步），外加每半年约 4–8 小时跟随 Codex rollout JSONL 与 `state_*.sqlite` 结构变化的维护；纯 Python 标准库，无托管与固定 API 费用。
- 价值锚点：真实案例中一条正在生成 18 页行程 PDF 的线程卡死后无法继续，恢复路径保住了交付物；provider 场景中切换中转站后 9 条旧线程打不开，同步后重新可访问。手工重新定位故障并重做收尾约 30–60 分钟/次，交付物重做成本更高。
- 价格位置：六维加权结果约 2.90/5。诊断与修复可复现、验收条件明确，但使用场景低频，且存在“直接放弃旧线程、新开线程收尾”这一替代路径，当前由维护者承担成本，作为免费公开入口。
- 证据边界：两个案例都带具体线程 id、原始报错与回读结果（18 页 PDF 重新生成、9 条 custom → litellm 且保留 2 条 built-in openai）；尚缺外部用户、不同 Codex 版本与 Windows / Linux 环境的样本。

## 六维评分

| 维度 | 分数 / 5 | 权重 | 加分事实 | 扣分事实 |
| --- | ---: | ---: | --- | --- |
| 实际结果价值 | 3.5 | 30% | 输出是可直接使用的诊断结论、恢复后的交付物路径与可继续的线程元数据，而不是一段建议 | 只在故障时刻产生价值，正常使用期间完全用不到 |
| 稀缺性与替代难度 | 3.5 | 20% | 同时覆盖悬挂 tool call 与 provider 绑定过期两类故障，并明确 paginated rollout 不可改写的边界 | 替代路径存在：放弃旧线程、从磁盘产物重新开工；单点替代门槛不高 |
| 质量证据与购买信心 | 3.5 | 15% | 两个真实案例含线程 id、原始报错、修复前后回读；源码校验通过且默认只读 | 尚无外部用户复现，未覆盖其他 Codex 版本与操作系统 |
| 价值飞轮潜力 | 1.5 | 15% | Profile 可沉淀语言与时区等偏好，故障手册会随案例增长 | 每次恢复彼此独立，线程内容不入库，用户之间没有网络效应 |
| 维护与交付效率 | 2.5 | 10% | 纯标准库、无凭据收集、无托管成本，支持边界清楚 | 依赖 Codex 内部 rollout 与 SQLite 结构，宿主升级时需要跟随适配 |
| 复制与渠道可控性 | 1.5 | 10% | 版本、CHANGELOG、案例与可信度卡形成一定信任差异 | MIT 公开源码，核心脚本短小，容易被重写或转发 |

加权总分约 2.90 / 5；当前适合免费入口与真实使用证据积累，不适合直接定价售卖。

## 买家得到什么

- 一条只读命令：解析 `codex://threads/<uuid>` 或线程 id，定位 rollout，报告 `dangling_calls`、`last_turn_error` 与 `poisoned` 判定。
- 一条修复命令：生成 `<rollout>.repaired.jsonl` 副本（默认不覆盖原文件；宿主未运行线程时才 `--write`，并保留 `.bak`）。
- 一条 provider 同步命令：先 `--json` 只读预演，列出过期的 `threads.model_provider`；`--apply` 前做 SQLite 一致备份，只同步当前配置已不存在的 provider，保留 built-in `openai` 历史，绝不改写 `sessions/*.jsonl`。
- 恢复优先级建议：先抢救磁盘交付物并在新线程收尾，只有在必须沿用同一线程时才改 rollout。
- 适用边界：只处理 Codex 会话持久化状态与 provider 绑定这两类故障；不管理 `config.toml` provider 定义、不修 arbitrary 软件错误、不做远程发布。

## 渠道与推广

- 在 LovStudio 官网免费提供，详情页突出“报错原文进、可继续路径出”，而不是罗列脚本参数。
- 试用入口先展示只读诊断命令与 JSON 报告，再展示修复副本与 provider 预演，让用户在无风险路径上建立信任。
- 内容侧用两个真实案例讲故事：一次保住 18 页交付物，一次把 9 条打不开的旧线程接回新 provider。
- 只有当出现托管巡检、团队共享会话修复服务或长期支持承诺时，重新评估付费结构。

## 风险、假设与复评

- 使用风险：修改运行中线程的 rollout 可能不生效（宿主内存缓存）；修复副本会丢弃未成功处理的尾部，因此交付物必须先在磁盘上确认。
- 假设：用户能提供线程 id 或 `codex://` 链接，并允许脚本读取本机 `~/.codex`。
- 证据缺口：外部用户复现、不同 Codex 版本、Windows / Linux 环境、长期 schema 稳定性与实际节省时间统计。
- 复评触发：累计 10 次外部真实使用、3 个非作者案例、Codex rollout / state 数据库结构变化、宿主校验语义变化或出现托管修复服务时复评。

## 机器可读摘要

```json
{
  "skill_id": "lov-fix-codex-session",
  "version": "0.2.0",
  "display_unit": "credits",
  "billing_model": "free_entry",
  "recommended_price_credits": 0,
  "launch_price_credits": 0,
  "price_range_credits": [0, 0],
  "weighted_score": 2.9,
  "channel": "LovStudio Skill Publisher",
  "assumptions": ["one stuck-thread recovery saves 30-60 minutes of re-diagnosis and safeguard work", "maintenance needs 4-8 hours per half-year following Codex schema changes"],
  "evidence_gaps": ["external users", "other Codex versions", "Windows and Linux coverage", "long-term rollout schema stability", "measured time savings"],
  "confidence": "case-backed",
  "review_trigger": "10 external real uses, three non-author cases, Codex rollout or state DB schema change, host validation change, or a hosted recovery service"
}
```
