# Electron / Tauri 运行时适配

公共生命周期契约相同，但 production API、退出事件和开发态 owner 不同。先识别运行时，再选择对应 adapter；不要把一个运行时的 API 名称机械翻译到另一个运行时。

## Production adapter

### Electron

在 main process 中集中进入完整重启。所有可取消检查必须先完成，因为 `app.relaunch()` 安排的后继实例没有 cancel API。

```ts
function relaunchPackagedElectron(): void {
  app.relaunch();
  app.quit();
}
```

`app.quit()` 保留 `before-quit`、`will-quit` 和窗口 `beforeunload`。若产品明确选择 `app.exit()`，应单独记录它绕过正常退出钩子的影响。

### Tauri 2

当退出清理依赖 `RunEvent::ExitRequested` 或 `RunEvent::Exit` 时，使用事件循环请求形式：

```rust
fn relaunch_packaged_tauri(app: &tauri::AppHandle) {
    app.request_restart();
}
```

Tauri 的 `restart()` 在主线程调用时不能保证退出事件被送达，可能直接重启进程；`request_restart()` 会把请求交回事件循环。不要在调用后继续执行依赖 Tauri runtime 的工作。

## Development adapter

### 复用持续存活的 renderer/WebView server

若 Vite 等 server 不属于即将退出的应用子树，并已通过 PID/父进程与端口验证会持续存活，只替换应用二进制：

- Electron：使用启动时保存的 Electron `execPath`/`args`，或由持续存活的 wrapper 接收 relaunch intent。
- Tauri：从 `current_exe` 启动新的 debug binary，再让旧 App 完成退出；必要时用独立 process group 防止 runner 回收新进程。
- 新实例仍须等待旧 single-instance lock 释放，不能只因为 server 存活就立即启动。

### 替换完整 wrapper 进程树

若 `electron-vite`、`tauri dev`、package-manager wrapper 同时拥有 server、main/Rust build 或 watcher，应用退出会带走依赖服务。此时使用 one-shot helper：

1. App 启动早期保存 wrapper executable、参数数组、cwd、稳定环境、main PID、owner PID 和端口。
2. helper 脱离旧 process group，等待旧 main/owner 消失、端口释放和 single-instance lock 可用。
3. 直接 spawn 保存的 executable 与参数数组；不要经过 login shell 或 `shell: true`。
4. helper 记录结果后退出，不成为长期 supervisor。

对于 npm 启动的 Tauri，可从启动契约捕获 Node executable 与 npm CLI，再以参数数组执行 `npm run tauri dev`；不要从 `target/debug/<app>` 的 argv 反推 wrapper。

### 复用 supervisor

若外层 supervisor 不会随 App 退出，给它显式的 `relaunch` / `user-quit` intent。不要同时启动 helper，否则会出现双 main、双 Vite 或端口竞争。

## Tauri 环境边界

Tauri helper 需要保留用户的稳定环境，例如 `PATH`、代理、registry、证书、`CARGO_NET_GIT_FETCH_WITH_CLI` 和项目配置。只移除已确认属于旧构建/子进程的注入变量，例如：

- Cargo compile invocation：`CARGO_MANIFEST_*`、`CARGO_PKG_*`、`OUT_DIR`、`PROFILE`、`TARGET`、`HOST`、`DEP_*`。
- Node/package lifecycle：`NODE_CHANNEL_FD`、`NODE_UNIQUE_ID`、`npm_lifecycle_*`、`npm_package_*`、`INIT_CWD`。
- 当前进程专用的 PID、socket、inspector、动态库 fallback 或 child channel。

这不是固定黑名单。每个项目都要比较首次启动和 helper 启动的环境键与构建指纹，证明某个键会污染下一次启动后再移除。

## Readiness adapter

| Runtime | 加载信号 | 失败信号 | 仍需组合 |
| --- | --- | --- | --- |
| Electron | load Promise、`did-finish-load` | `did-fail-load` | 显示/聚焦、应用 health signal |
| Tauri | `Builder::on_page_load` / WebView `PageLoadEvent::Finished` | 前端 error event、启动日志或 health timeout | 正确 WebView label/URL、显示/聚焦、应用 health signal |

Tauri 的 `PageLoadEvent::Finished` 证明 WebView 导航完成，不单独证明业务初始化完成。若 App 有数据库恢复、权限检查、索引或插件加载，应增加应用级 ready 事件。

## Tauri 验收补充

- 对比旧、新 debug binary PID，同时对比 `tauri dev` owner 和 Vite 端口 owner。
- 完整 wrapper 重启时三者都应按设计替换；只重启 binary 时 server owner 应保持不变。
- 源码未变时，重启日志不应出现依赖安装、全量 Rust rebuild 或第二套 Vite。
- macOS 存在 stable/debug 同 bundle ID 时，GUI 自动化必须按精确可执行路径或已确认 PID 定位，不能只按 bundle ID。

## 官方依据

- [Electron `app.relaunch()` / `app.quit()`](https://www.electronjs.org/docs/latest/api/app)
- [Tauri `AppHandle::restart()` / `request_restart()`](https://docs.rs/tauri/latest/tauri/struct.AppHandle.html)
- [Tauri `Builder::on_page_load`](https://docs.rs/tauri/latest/tauri/struct.Builder.html#method.on_page_load)
