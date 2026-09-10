---
name: lov-check-balance
description: >
  一条命令查清 Claude、Codex、DeepSeek 等 agent 账号的剩余额度与重置时间，
  合并官方订阅窗口、API 余额、本地网关消费与消耗速率；用户说“查我的额度”
  “还有多少用量”“什么时候重置”，或问 how much quota is left 时使用。
license: MIT
compatibility: "Portable Agent Skills format. Python 3.8+ standard library only. macOS Keychain, Codex auth.json, cc-switch SQLite, and LiteLLM request logs are optional inputs; an unavailable source degrades into a labelled gap instead of failing the run."
metadata:
  author: skill-publisher
  version: "0.1.0"
  card_standard: lovstudio/skill-card/v1
  content_class: deterministic-output
  tags:
    - quota
    - usage
    - rate-limit
    - subscription
    - agent-account
---

# 额度体检 · Check Balance

把散落在不同 agent 里的「还剩多少、什么时候重置」收敛成一张只读体检表：官方
订阅的窗口额度、API 平台的预付余额、本地网关的真实消费，以及按当前强度还能用多久。

## Triggers

### Activate when

- 用户说“查一下我的额度”“Claude / Codex 还有多少用量”“什么时候重置”“余额还够用几天”。
- 用户要在被限流或余额见底前收到提醒，或需要把额度纳入定时巡检。
- User asks "how much quota do I have left", "when does the Codex limit reset", or "check the API balance".

### Do not activate when

- 用户要管理、轮换或新增 API Key 本身；交给 `lov-env-management`，本 Skill 只读现有凭据。
- 用户要设置定时执行与通知渠道；交给 `lov-yoda-automation`，本 Skill 只提供 `--json` 输入。
- 用户要清理磁盘空间或归档文件；交给 `lov-clean-mac`。
- 用户要充值、购买或升级订阅；本 Skill 只报告现状，不执行任何计费操作。

## 输出契约

每次运行输出同一份结构，默认渲染为文本表，`--json` 输出机器可读版本：

- `providers[]`：每个账号的 `id`、`status`（ok / expired / unavailable）、计划、
  窗口用量与重置时间，或余额与币种。
- `burn_rate`：可选。`--watch` 二次采样后给出每小时消耗与剩余可用天数。
- `alerts[]`：已用满的窗口、低于阈值的余额、未设置日/月限额的 provider。

只读不变量：脚本不刷新 token、不写入任何凭据、不打印密钥；缺失的来源只标记
`unavailable` 并给出补救提示，不影响其它 provider。

## User Profile（跨 session）

本 Skill 在 `skill.yaml` 中声明 `user-profile/v1`。运行时按「当前请求 → 项目
上下文 → Skill 记录 → 共享 preferences → 共享 user/workspace → 安全默认值」
解析。用户直接说出的长期偏好（例如网关日志路径、余额告警阈值）通过
`scripts/profile_store.py record --skill-id lov-check-balance --path records.<字段>
--value <值> --confirm` 写回，并回报保存路径。凭据本身永远不写入 Profile。

## Skill Group Composition

先读 `references/skill-composition.md`。相邻能力以可选交接为主：上游
`lov-env-management` 负责凭据生命周期，下游 `lov-yoda-automation` 负责定时与
通知；本 Skill 不隐藏依赖任何 sibling。

## Workflow（MANDATORY）

### Step 0: 解析运行上下文

- 优先使用宿主提供的 `SKILL_DIR`，否则按当前 Skill 上下文推断安装目录。
- 确认 `scripts/check_balance.py` 与 `references/providers.md` 存在，缺失则报出
  期望的相对路径并停止。
- 解析 Profile：`--profile` 参数 → `LOVSTUDIO_PROFILE` → 共享 Profile 默认路径。

### Step 1: 执行探测

```bash
python3 scripts/check_balance.py \
  --gateway-log "$GATEWAY_LOG" \
  --min-balance-cny "${MIN_BALANCE_CNY:-50}"
```

- 只查某一类账号时用 `--only codex`、`--only deepseek`，可重复。
- 需要结构化下游消费时加 `--json`。
- 结果先按 `references/providers.md` 核对每个 provider 的来源与重置语义。

### Step 2: 需要速率时二次采样

```bash
python3 scripts/check_balance.py --watch 120 --json
```

- 采样窗口建议 ≥120 秒：余额按批次结算，短窗口的隐含汇率不可作为结论。
- 余额未变化时脚本自动回退到网关计价估算，并标注 `estimate_basis`。

### Step 3: 交叉验证与汇报

- 官方订阅报告「已用百分比 + 重置时间」，预付余额报告「剩余金额 + 消耗速率」。
- 用网关消费与余额变化互相校验；两者口径冲突时同时列出，不擅自取一个当真值。
- 汇报最小充分集合：每个账号的剩余、重置时间、数据来源，以及需要用户动作的项。

## Dependencies

- Python 3.8+（仅标准库：urllib / sqlite3 / subprocess / json）。
- 可选输入：macOS Keychain、`~/.codex/auth.json`、cc-switch SQLite、LiteLLM 请求日志。
- 无第三方依赖、无需网络写权限；未配置的来源按不可用处理。
