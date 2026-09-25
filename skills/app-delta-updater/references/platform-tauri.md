# Tauri 2 自动更新契约

## 能力边界

Tauri 2 官方 updater 在 macOS、Windows 与 Linux 上消费签名更新包。默认产物是平台完整包，
`latest.json` 中的平台条目也不表达源版本，因此没有独立差分服务时应称为“签名自动更新”。

## 运行时接线

1. Rust 注册 `tauri-plugin-updater` 与 `tauri-plugin-process`。
2. JavaScript 使用 updater `check()`，给检查与下载设置超时，并保证单飞。
3. capability 开放 updater 的 check/download/install 与 process restart。
4. macOS/Linux 安装返回后显式 relaunch；Windows 按插件当前安装器语义处理退出或重启。
5. 将检查、下载、安装交接和重启后版本分开显示。

## 构建与更新源

- `bundle.createUpdaterArtifacts` 为 `true`。
- updater 配置包含公开 endpoint 与对应私钥的公钥。
- CI 通过 `TAURI_SIGNING_PRIVATE_KEY` 提供私钥；若私钥受口令保护，再提供
  `TAURI_SIGNING_PRIVATE_KEY_PASSWORD`。日志只报告 secret 名称和是否存在。
- 使用 `tauri-action` 向已有 Release 上传时，同时传入 `releaseId` 和 `tagName`，避免生成的
  更新 URL 意外指向 `releases/latest`。
- 多平台构建不得并发写同一个 `latest.json`：串行上传，或在所有平台产物齐备后由单独的
  汇聚 job 生成一次完整 manifest，并要求所有计划平台存在。
- 当 action 生成按安装器区分的平台键时，核对 `tauri-plugin-updater` 是否支持该 manifest
  形状；升级 action 或插件前先在真实目标平台回读。
- 先签名/公证最终产物，再生成 manifest；缺少 `.sig` 或目标架构时停止发布。

## 增量扩展

若未来接入差分后端，应新增明确的源版本、目标版本、架构、摘要、长度和差分签名契约，
并确认客户端安装器真的消费差分字节。仅缩小压缩包或使用 HTTP Range 不构成增量更新。
