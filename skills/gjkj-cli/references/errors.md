# 返回码与常见错误

成功：Open API 的 `code` 为 `"0000"`、`message` 为 `success`（个别文档写 `msg` 或 `code=200`，以 `0000` 为准）。

| 现象 | 含义 | 处理 |
| --- | --- | --- |
| `A001` | 缺少鉴权头 | 没读到密钥：跑 `doctor`，按 auth.md 存钥匙串或设环境变量 |
| `A003 token expired` | 密钥无效或过期。网关对认不出的密钥也回这个码，不一定是真过期 | `doctor` 看 `keychain_length`：长度不对就重存；长度对就到控制台确认密钥是否被删或过期，新建后重存 |
| Swagger 代理返回「代理进程没有大模型 API Key」 | 调的是 `/v1/*` 接口，需要另一把大模型 Key | 按 auth.md 建大模型 Key 并存 `suanli-llm-key` |
| 大模型接口 `insufficient_quota`「用户余额不足」 | Key 有效，但账户余额或该 Key 的额度为 0；连 `llm-list-models` 也要求有余额 | 用户在控制台充值或调高 Key 的额度 |
| 大模型接口 HTTP 400「缺少用户凭证」/ 401 | 没带 Authorization / Key 无效 | 同上，检查 `suanli-llm-key` |
| 写操作被 `gjkj_cli.py` 拒绝 | 没有带 `--approved` | 先 `--dry-run` 给用户看，拿到原话同意再调 |
| Swagger 代理 403 | 代理默认拒绝写操作 | 仍按逐次确认的规则在 CLI 里调；确需在页面调试时用户自己加 `--allow-write` 重启代理 |
| 本机时间不准导致签名失败 | `timestamp` 与网关时间偏差过大 | 用 `curl -s https://cloudflare.com/cdn-cgi/trace` 的 `ts=` 比对本机时钟 |

接口只有文档证据（`ops` 里没有 `V`）时，若返回结构与文档不同，如实报告差异，不自行猜补字段。
