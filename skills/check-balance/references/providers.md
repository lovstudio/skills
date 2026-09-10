# Provider 探测契约

每个 provider 独立探测。凭据只用于一次只读请求，不落盘、不回显；缺失即标记
`unavailable` 并给出补救提示。

## codex — ChatGPT / Codex 官方额度

- 凭据来源：`~/.codex/auth.json` 的 `tokens.access_token`，或 cc-switch 数据库
  `providers.app_type='codex' and id='default'` 里的 `auth.tokens`。
- 端点：`GET https://chatgpt.com/backend-api/wham/usage`，请求头
  `Authorization: Bearer <access_token>` 与 `chatgpt-account-id: <account_id>`。
- 关键字段：`plan_type`、`rate_limit.primary_window.used_percent`、
  `limit_window_seconds`、`reset_at`、`reset_after_seconds`、`limit_reached`、
  `additional_rate_limits[]`、`credits`。
- 重置语义：窗口按滑动周期滚动，`reset_at` 是绝对时间戳；`used_percent=100`
  但 `limit_reached=false` 表示额度已耗尽但服务端尚未硬拦。
- 注意：Codex 桌面版若被配置为第三方 provider（例如本地 LiteLLM），不会消耗
  官方窗口额度，此时应结合 `gateway` 与 `cc-switch` 一起解读。

## claude — Claude 官方订阅

- 凭据来源：macOS Keychain 服务 `Claude Code-credentials`（可用
  `--claude-keychain-service` 覆盖），或 `~/.claude/.credentials.json`。
- 判据：`claudeAiOauth.expiresAt` 早于当前时间即判定过期，直接报告
  `expired`，不尝试刷新 token，避免让用户的登录态失效。
- 端点（凭据有效时）：`GET https://api.anthropic.com/api/oauth/usage`，
  请求头 `anthropic-beta: oauth-2025-04-20`。
- 解析方式：遍历响应里含 `utilization` 的对象作为窗口，读取 `resets_at`；
  兼容 `five_hour`、`seven_day`、模型级窗口等命名。
- 重置语义：5 小时与 7 天窗口各自滚动重置。

## deepseek — 预付余额

- 凭据来源：环境变量 `DEEPSEEK_API_KEY`，或 Keychain 服务
  `codex-litellm-deepseek`（account `deepseek`）。
- 端点：`GET https://api.deepseek.com/user/balance`。
- 关键字段：`is_available`、`balance_infos[].currency`、`total_balance`、
  `granted_balance`、`topped_up_balance`。
- 重置语义：按量扣费，无固定重置窗口，充值即续。
- 计费提示：官方价格区分峰值与非峰值，峰值约为非峰值的两倍；缓存命中价格
  远低于缓存未命中，长上下文重复请求的成本主要由缓存命中决定。

## openrouter — 额度与剩余

- 凭据来源：环境变量 `OPENROUTER_API_KEY`，或 Keychain 服务
  `openrouter-api-key`。
- 端点：`GET https://openrouter.ai/api/v1/key`。
- 关键字段：`data.usage`、`data.limit`、`data.limit_remaining`、
  `data.limit_reset`。`limit_reset` 为 `daily`、`weekly`、`monthly` 时表示
  对应的重置周期，为空则表示未设置周期限额。

## gateway — 本地 LiteLLM 消费

- 输入：`--gateway-log`、环境变量 `LITELLM_REQUEST_LOG`，或 Profile 的
  `records.gateway_log`，指向 `requests-brief.jsonl` 一类的 JSONL。
- 计算：按 `start_time` 的日期分组，累加 `cost`、`usage.input_tokens`、
  `usage.output_tokens`、`usage.input_tokens_details.cached_tokens`。
- 用途：与预付余额的变化互相校验，并区分「今天」与「累计」消费。
- 注意：网关的 `cost` 是本地计价估算；它与真实扣费之间的比例可用
  `--watch` 采样交叉验证，采样窗口短于 120 秒时不要采信隐含汇率。

## cc-switch — 代理用量与限额

- 输入：`--cc-switch-db`，默认 `~/.cc-switch/cc-switch.db`。
- 计算：`proxy_request_logs` 按 app 与 provider 汇总次数与成本；
  `providers` 中当前 provider 的 `limit_daily_usd`、`limit_monthly_usd`。
- 重置语义：限额字段非空时，日报窗口按自然日、月报窗口按自然月重置；
  两者都为空表示没有预算护栏，脚本会在 `alerts` 中提示。
- 隐私：只读取聚合结果，不读取或输出任何 token 字段。

## 阈值与退出码

- `--min-balance-cny` 或 Profile 的 `min_balance_cny` 控制余额告警。
- 退出码：`0` 正常；`1` 与 `--strict` 连用表示有来源不可用；`2` 表示所有
  探测都失败（例如完全离网）。
