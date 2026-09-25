# 机制与真实证据

## 为什么会出现 provider 不统一

Codex 把 provider 分成两层：

1. **配置层**：`~/.codex/config.toml` 的 `model_provider` 默认值与
   `[model_providers.<id>]` 定义。桌面 App、普通 CLI、app-server 都从这里解析。
2. **会话层**：每条 thread 在创建时把当时的 provider id 持久化下来，桌面 App 恢复
   会话时按这个 id 去找配置定义。

Yoda 这类集成为了让历史在不同模型接入之间保持连续，会刻意使用一个稳定的
provider id（源码注释写明「Codex filters its history by the exact model_provider
string」），并在启动 Codex 时用 `-c model_provider=yoda` 之类的参数注入完整定义。
这些参数只存在于该次启动进程，不写进 `config.toml`。

于是出现两条路径不一致：

| 入口 | provider 来源 | 能看到 `yoda` 吗 |
| --- | --- | --- |
| Yoda 启动的 Codex | 启动参数 `-c` 注入 | 能 |
| 桌面 App / 普通 CLI | `~/.codex/config.toml` | 不能，除非配置里定义了 |

切换器类工具重写 `config.toml` 时也会制造同类问题：配置里引用了尚未定义的
provider，或历史 thread 的 provider 定义被删掉。

## 失败链路

```text
用户在桌面 App 打开历史会话
  -> thread/resume(threadId)
  -> app-server 读取该 thread 持久化的 model_provider
  -> 在 config.toml 中找不到定义
  -> JSON-RPC -32600 invalid_config
  -> 界面提示这条会话打不开
```

典型报错文本：

- `failed to load configuration: Model provider \`yoda\` not found`
- `Request failed ... failureReason=invalid_config`
- `Failed to resume conversation ... errorMessage="failed to load configuration: ..."`
- `Failed to load older thread history` 同因
- 中文界面常见「这条会话无法恢复 / 打不开」的说法

## 持久化的两处位置

1. `~/.codex/state_5.sqlite` 的 `threads.model_provider`：会话索引，App 恢复会话时
   直接读它。
2. rollout JSONL 首行 `session_meta` 的 `payload.model_provider`：会话文件自身的
   元数据，重建历史时可能覆盖索引值。

两者可能单独过期：本机抽样就发现一条 thread 索引是 `lovbrowser`，rollout 里是
`openai`。只改一处会在下一次恢复时重新出现不一致。

## 本机证据（2026-09-12 只读扫描）

配置：`~/.codex/config.toml` 只定义了 `custom`，`model_provider = "custom"`。

thread 索引：

| provider | 总数 | 活跃 | 归档 | 最近使用 |
| --- | --- | --- | --- | --- |
| `yoda` | 3097 | 1050 | 2047 | 2026-09-11 20:44 |
| `custom` | 9 | 9 | 0 | 2026-09-12 09:21 |
| `lovbrowser` | 9 | 5 | 4 | 2026-07-27 16:00 |
| `nebula` | 1 | 0 | 1 | 2026-07-26 14:54 |
| `xxx` | 1 | 0 | 1 | 2026-09-05 17:59 |

桌面 App 日志（`~/Library/Logs/com.openai.codex`）：

- `yoda`：13 次 `Failed to resume conversation`，共 103 处命中，分布 10 个日志文件，
  最后一次 2026-09-12。
- `custom`：3 次 resume 失败，最后一次 2026-09-10。

核心日志（`~/.codex/logs_2.sqlite`）：`custom` 在 2026-09-09 触发 8 次
`failed to load configuration` 警告，来自 TUI recap 请求。

这些统计只说明「provider 解析失败」，不区分具体是哪个模型或哪次请求；判定时以
thread 索引和当次日志为准。

## 版本边界

- 本机验证版本：codex-cli 0.153.4、Codex Desktop 26.903.71938、macOS。
- `state_5.sqlite` 的表结构、rollout 首行字段、`codex doctor` 输出都随版本变化；
  升级 Codex 后重新跑一次只读诊断再修。
- provider id 与配置语义属于兼容合同：不要为了「统一」把仍在使用的 `yoda`、
  `custom` 随机改名，优先补定义。
