# Electron 自动更新与 Sparkle delta

## 平台选择

- macOS：Electron 原生 `autoUpdater` 使用 Squirrel.Mac。只有项目明确接入
  Sparkle-compatible 包装、稳定签名与架构专属 appcast 时承诺 Sparkle delta；普通
  Squirrel.Mac 完整包更新仍是自动更新，但不是 Sparkle delta。
- Windows：按项目实际使用的 Squirrel.Windows、MSIX、NSIS/MSI 与 blockmap 能力判断，逐平台报告。
- Linux：Electron 原生 `autoUpdater` 没有内置支持；按发行版包管理器或项目实际 updater
  单独报告，不将其默认视为桌面自更新。
- 下载完整安装包仍是自动更新，但不属于 delta。

## Sparkle delta 契约

- 每个 delta 对应一个明确源版本、目标版本和架构。
- appcast 的 URL、长度与签名必须对应最终已签名/公证产物。
- 检查请求有截止时间，支持时把取消信号传到底层网络调用。
- delta-only 模式发现完整包回退时停止当前链路并显示手动安装路径。
- 本地 feed 代理只绑定 loopback，只代理已验证 URL，保留 Range/If-Range/Content-Range，
  并在安装完成或失败后关闭。

## 安装交接

下载完成后等待原生 helper 确认接手安装；在此之前保持进程存活。应用自己的清理、数据库
flush 和窗口关闭应在交接前完成。重启后重新读取 bundle 版本作为安装完成证据。
