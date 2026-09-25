# 桌面应用重新启动契约

## 四种不同动作

| 用户动作 | 正确目标 | 典型实现 | 后继进程 |
| --- | --- | --- | --- |
| 刷新当前界面 | renderer/WebView | Electron `webContents.reload()` 或 Tauri WebView `reload()` | 不创建 |
| 重启整个应用 | app core + 新进程 | runtime production adapter，或开发态 helper | 创建一个 |
| 退出应用 | 当前完整进程树 | Electron `app.quit()` 或 Tauri `app.exit(0)` | 不创建 |
| 安装已下载更新 | updater handoff | 完成 staging/cleanup 后交给 updater | 由 updater 控制 |

不要用刷新冒充重启，不要让重启逻辑抢走 updater，也不要把用户退出识别为需要自动恢复的崩溃。

## 开发态启动拓扑

先识别进程所有权，再选择实现。

| 拓扑 | 识别方式 | 重启策略 |
| --- | --- | --- |
| 应用自包含 | Electron `execPath/args` 或 Tauri `current_exe` 足以恢复 app 与界面 | 使用对应 runtime adapter 只替换应用进程 |
| 外部 dev server 持续存活 | server 不属于当前应用子树 | 只替换应用进程并复用 server |
| wrapper 共同拥有工具链 | npm/pnpm、electron-vite、`tauri dev` 或 concurrently 同时拥有 server、main/Rust build 或 watcher | 先核对 owner 退出策略，再由既有 owner 或 one-shot helper 替换整树 |
| supervisor/daemon 托管 | 外层进程负责崩溃恢复或保活 | 给 supervisor 明确 relaunch intent；用户退出时关闭保活 |

不要把“当前应用二进制可再次执行”误判为“整个开发环境可恢复”。若 Vite、main/Rust compiler 或 preload watcher 会随旧父进程退出，直接重启 binary 可能得到白屏、旧 bundle 或断开的 dev URL。运行时选择细节见 [runtime-adapters.md](runtime-adapters.md)。

## 集中 relaunch plan

在 main process 启动早期保存不可变计划，而不是点击菜单时读取已变化的环境。

```ts
type ShutdownIntent = "user-quit" | "relaunch" | "install-update";

interface RelaunchPlan {
  runtime: "electron" | "tauri";
  execPath: string;
  args: string[];
  cwd: string;
  env: NodeJS.ProcessEnv;
  owner: "electron" | "dev-wrapper" | "supervisor";
}
```

计划至少保存：

- 实际可执行文件和参数数组，不保存需要 shell 再解析的拼接字符串。
- Electron 自重启使用 `execPath = process.execPath` 与 `args = process.argv.slice(1)`；wrapper 重启保存 wrapper 自己的 executable/args，不把 `process.argv[0]` 当应用参数传回去。
- 正确工作目录；worktree、monorepo package 和安装版目录必须可区分。
- App 启动时的稳定环境快照。
- 谁拥有 dev server、watcher、PTY、child process 和 single-instance lock。

生产态统一从一个 app-core 函数进入。Electron 示例：

```ts
function relaunchPackagedApp(): void {
  app.relaunch();
  app.quit();
}
```

Tauri 2 若依赖退出事件清理，使用 `AppHandle::request_restart()`；主线程上的 `restart()` 不能保证退出事件送达。开发态只有在依赖服务会继续存活时，才直接替换应用 binary。wrapper 会随旧 App 收束时，交给 one-shot helper 等待旧 PID、owner、端口和锁真实释放后启动计划中的命令；wrapper 不会收束时，复用该 owner 的 relaunch 通道或让外部 supervisor 替换整树，不要再启动一套 dev command。

## 可取消退出

Electron 的 `app.quit()` 会运行窗口的 `beforeunload`，窗口可以取消退出。先完成未保存内容确认和可能阻止退出的检查，再调用 `app.relaunch()`：

- 把确认、异步清理和状态持久化放在“安排后继实例”之前。
- 只在退出已获准时设置 `ShutdownIntent = "relaunch"` 和一次性 guard。
- 在调用 `app.relaunch()` 前发生失败或取消时，撤销 guard 与 relaunch intent。所有可取消步骤必须止于这里。
- 一旦调用 `app.relaunch()`，即进入没有 cancel API 的提交阶段；保证旧进程随后必然退出。若仍无法排除窗口取消退出，改由外部 helper 在旧 PID 已真实退出后启动新实例，不要预先调用 `app.relaunch()`。
- 对必须绕过窗口确认的产品流程单独评审 `app.exit()`；它会跳过 `before-quit` / `will-quit` 和窗口卸载处理，不作为普通重启默认值。

## Shutdown intent

在 `before-quit` 之前设置 intent，并让所有退出钩子读取同一个状态。

- `user-quit`：关闭 children/PTY/server，取消 helper，不创建后继实例。
- `relaunch`：完成重启所需清理，只安排一个后继实例。
- `install-update`：停止普通 relaunch，把退出控制交给 updater。

区分预期退出与崩溃恢复。watcher、LaunchAgent、supervisor 或自恢复逻辑必须知道用户主动 `Cmd+Q`，否则会表现为“退出后不断重启”。

## Single-instance 与端口

- 在旧实例退出前安排计划，但不要过早启动替代 Electron 进程。
- 等待旧 PID 消失和 single-instance lock 释放，避免替代实例进入 `second-instance` 后直接结束。
- 对本地 server 轮询真实监听状态；处理 IPv4 与 IPv6，不使用固定延时猜测释放时间。
- 对等待设置上限。超时后记录旧 PID、占用端口的 PID 和命令，并停止创建更多 helper。
- 给菜单动作加一次性 guard，避免双击生成两个替代进程。

## 菜单文案

- “重新加载”用于当前界面，保留标准 reload shortcut。
- “重启 {App 名称}”用于完整应用。
- “退出 {App 名称}”不安排后继实例。
- “安装并重启”只在更新包已准备好时出现。

## 验收证据

至少比较旧、新实例的 PID 与启动时间。若系统可能存在同 bundle ID 的安装版和开发版，再比较：

- 可执行文件路径。
- 工作目录和启动参数。
- 父进程/进程组。
- renderer/dev-server 端口所有者。
- Electron 的 load Promise / `did-finish-load` 或 Tauri 的 `PageLoadEvent::Finished` 是否成功，窗口是否已显示/聚焦，以及应用级 health signal 是否 ready；同时记录对应失败/超时信号。Electron 的 `ready-to-show` 仅作为可选信号。

另外验证用户退出：触发 `Cmd+Q` 后，App、helper、child process 和端口应按既定策略收束，不出现自动拉起。

## 官方依据

- [Electron `app`：`relaunch`、`quit` 与可取消退出](https://www.electronjs.org/docs/latest/api/app)
- [Electron `BrowserWindow`：加载 Promise、`ready-to-show` 与 `paintWhenInitiallyHidden`](https://www.electronjs.org/docs/latest/api/browser-window)
- [Node.js `child_process`：detached child 与 `unref()`](https://nodejs.org/api/child_process.html)
- [Tauri `AppHandle`：`restart` 与 `request_restart`](https://docs.rs/tauri/latest/tauri/struct.AppHandle.html)
- [Tauri `Builder::on_page_load`](https://docs.rs/tauri/latest/tauri/struct.Builder.html#method.on_page_load)
