# 报错说模型名为空，真正没关掉的是 WebSocket

本地 ChatGPT 桌面版每发一轮就失败一次，返回的是这一句：

```json
{"error":{"code":"","message":"Model name not specified, model name cannot be empty","type":"new_api_error"}}
```

模型名一直在那儿。会话日志第二行的 `thread_settings_applied` 写着 `model: "gpt-5.6-sol"`，中转的 `/v1/models` 里也有这个 id。报错落在模型名上，问题不在模型名。

## 几条 curl 就把范围压到传输层

这台机器上的 Codex 没走官方账号，`~/.codex/config.toml` 里的 `model_provider` 指向一张自己维护的 provider 表，`base_url` 是自建的 new-api 中转，`wire_api = "responses"`。

拿同一个 key、同一个 `gpt-5.6-sol`，换三种发法：

| 发法 | 结果 |
|---|---|
| `POST /v1/chat/completions` | 正常返回 |
| `POST /v1/responses`，`input` 传字符串 | `Input must be a list` |
| `POST /v1/responses`，`input` 传列表 | 正常流式返回 |
| WebSocket upgrade `/v1/responses` | `Model name not specified` |

中间那条 `Input must be a list` 其实是最有用的一条：中转已经读到了 body 里的 `model`，走完了鉴权和路由，只是在校验 `input` 结构时才拦下来。模型名解析这一段是通的。

最后一条无论带不带 `?model=gpt-5.6-sol`，回的都是同一句话。

![左侧一张 provider 配置表分出两条路径，上路 HTTP POST 经中转从 body 取到模型名后返回 200，下路 WebSocket upgrade 在中转取不到模型名，返回 Model name not specified](PLACEHOLDER_01)

_Codex 用哪条路出去，由 provider 表里的 supports_websockets 决定；中转只实现了上面那条。_

第三方中转普遍只把 `/v1/responses` 当普通 HTTP 接口来转，WebSocket 那条分支要么没实现，要么按另一套约定取参数。Codex 却按配置认为对面支持 WS，于是发了一个 upgrade 请求，撞在中转的 WS 入口上，被回了一句关于模型名的话。

## 那行配置是从官方模式继承来的

翻到 provider 表本体，混得很明显：

```toml
[model_providers.yoda]
name = "OpenAI"
requires_openai_auth = false
supports_websockets = true      # 官方账号模式的键
wire_api = "responses"
base_url = "https://…"          # 中转模式的键
experimental_bearer_token = "…"
```

上半截是官方账号模式写的，下半截是中转模式写的。四天前的配置备份里，这张表还是纯粹的官方模式版本，`requires_openai_auth = true`。中间某次切换只覆盖了它关心的那几个键，`supports_websockets = true` 原地留了下来。

写这张表的代码本身没问题。中转模式的构造函数会先把整张 `[model_providers.*]` 删掉再重建，重建时压根不写 `supports_websockets`；它的校验函数甚至要求 `requires_openai_auth` 必须是 `undefined`、`name` 不能是 `OpenAI`——线上这张表连自己的校验都过不了。所以合并动作发生在这段代码之外。

## 修成显式 false，而不是删掉那一行

删掉那行只能保证下一次由我们重建的表是干净的。任何做键级合并、而不是整表重写的写入方，都会把旧值原样带过来——这次就是这么坏掉的。

所以改法是把它钉死：

- 中转 provider 表里显式写 `supports_websockets = false`，不再依赖"没写就是关"；
- 校验从"允许缺省"升级成硬断言，值不是 `false` 直接抛错，让混入的 `true` 在写入时就炸，而不是等用户发消息才炸；
- 每次启动传的 `-c` 覆盖参数里也带上同一条，文件被外部改写时还有一层兜底；
- 补一条回归用例：官方模式 → 中转模式切换后，配置里必须是 `false`、不能出现 `true`。

官方账号那条路仍然是 `true`，它对着真正的 OpenAI，WebSocket 是能用的。关掉的只是中转这一侧。

改完 80 个用例通过，类型检查干净。桌面端要重启一次才会读到新配置——它的进程比这次修复早启动九分钟。

## 还没查清的一段

谁把官方模式的键和中转模式的键合进了同一张表，我没查出来。嫌疑最大的是桌面端自己回写 `config.toml`，因为 `requires_openai_auth = false` 这种显式假值不像是我们写的，更像是某个反序列化过程把默认字段补全后原样落盘。但我手上没有能指认它的证据链，只有一个时间点对不上的备份文件。

配置项的默认值在只有一种上游时无所谓，接了第二种上游就成了会串味的状态。`supports_websockets` 这类"对面支不支持某种传输"的开关，只要有一个 provider 需要它是 `false`，就不该留成隐式默认。
