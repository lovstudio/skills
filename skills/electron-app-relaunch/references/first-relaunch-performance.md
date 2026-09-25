# 第一次重启性能诊断

## 为什么必须分开测量

“第一次很慢、后面很快”说明系统存在一次性的状态切换。常见原因不是 Electron/WebKit 的窗口动画，而是两次启动使用了不同的构建指纹、父进程拓扑、端口所有者或缓存状态。

把第一次、第二次和第三次完整重启分别记录。不要只报告热重启平均值，也不要直接把首轮差异描述为正常冷启动。

## 建立时间线

在 main process 和 helper 中使用同一个单调时钟或带毫秒的时间戳，记录以下里程碑：

1. 菜单事件收到。
2. relaunch plan/guard 建立。
3. `before-quit` 与 `will-quit` 开始、完成。
4. 旧 desktop main PID 消失。
5. single-instance lock 与端口释放。
6. helper 启动真实 dev command。
7. dev server ready。
8. main bundle/build ready。
9. 新 desktop main PID 出现。
10. Electron 的 `app.whenReady()`、load Promise/`did-finish-load`，或 Tauri 的 `PageLoadEvent::Finished`；再记录窗口显示/聚焦和应用级 health signal，同时记录失败/超时。Electron 仅在窗口配置支持时记录 `ready-to-show`。

用最长区间确定优化对象。只统计新 PID 出现会低估白屏时间；只统计窗口出现又可能漏掉不可交互状态。

## 症状与定位

| 现象 | 优先检查 | 典型修复 |
| --- | --- | --- |
| 首轮出现 compile/rebuild，后续 cache hit | 初次启动与 helper 的 cwd/env/command 差异 | 固化 startup plan，归一化运行时变量 |
| App 很快退出，但端口数秒后才释放 | wrapper/child tree 的 shutdown | 明确进程组，等待真实 PID/port，缩短轮询 |
| server ready 很快，窗口仍白屏 | preload/main bundle、Tauri dev URL 或 runtime identity | 验证正确实例、URL 和 runtime load-finished 信号 |
| 新 PID 很快出现，窗口很晚可交互 | 同步初始化、数据库恢复、扩展扫描 | 延后非关键任务，增加 readiness 里程碑 |
| `Cmd+Q` 后再次启动 | watcher/supervisor 把用户退出当崩溃 | 传递 `user-quit` intent，取消后继计划 |
| 第二个实例出现后立即消失 | single-instance lock 尚未释放 | helper 等旧 PID/lock，再启动一次 |

## 比较启动环境

在 App 启动早期保存环境基线。点击重启时不要直接把已运行数分钟后的 `process.env` 原样交给下一套构建工具。

比较两次启动的环境键和不可逆摘要，避免把 token、cookie、代理密码或路径中的敏感片段写进日志。重点关注：

- `PATH`、cwd、Node/Electron/Tauri 可执行文件和 package-manager 版本。
- `ELECTRON_RUN_AS_NODE`、`NODE_CHANNEL_FD`、`NODE_UNIQUE_ID`、inspector IPC 等 child/runtime 注入变量。
- 临时 PID、socket、port、session、watcher 与 dev-server 变量。
- `npm_lifecycle_*`、`INIT_CWD` 和 wrapper 自定义变量是否从一套启动方式切换到另一套。
- 原生模块、Cargo 或附属工具链注入的 build output、manifest path、deployment target、compiler flag 与动态库路径。

不要全量清空环境。保留用户明确配置的 PATH、代理、证书、registry、编译器和项目变量，只移除已证明是当前进程运行时产物的键。

## 避免 Shell 引入第二套环境

优先直接 spawn 可执行文件与参数数组。一次性 helper 必须解除父进程引用并在需要时进入独立 process group；有意长期托管的 supervisor 则保留引用，并承担退出意图、日志和回收责任：

```ts
const child = spawn(plan.execPath, plan.args, {
  cwd: plan.cwd,
  env: plan.env,
  detached: true,
  stdio: "ignore",
});
child.unref();
```

需要等待旧 PID/owner/端口时，让 one-shot Node/Rust helper 执行有界轮询，再直接 spawn 计划命令。先确认旧 wrapper 是否会收束；若不会，复用 owner/supervisor 的 relaunch 通道，避免重复 Vite、watcher 或端口冲突。避免：

- `sh -lc`、`zsh -lic` 等 login shell。
- `shell: true` 与一整条字符串命令。
- 重启前后切换 pnpm/npm/bun 或 Node/Electron 版本。
- helper 再包一层与初次启动不同的 wrapper。

若项目确实依赖 shell 初始化，明确加载哪一个初始化文件，并让首次启动与重启使用同一条入口。

## 去掉固定等待

固定 `sleep 1` 会给每次重启永久增加一秒，也仍可能在慢机器上失败。改为短间隔、有上限的条件等待：

- 旧 PID 是否消失。
- 目标端口是否不再监听。
- single-instance lock 是否可获得。
- dev server 是否开始返回正确页面。

记录尝试次数和总等待时间。超时后保持失败可诊断，避免循环创建 helper。

## 并行与预热

- 若 main build 与 renderer server 互不依赖，并行启动；在窗口加载前统一等待 readiness。
- 仅预热确定会在每次启动使用的昂贵模块、native addon 或索引；不要用隐藏的后台全量构建掩盖错误指纹。
- 源码未变化时，重启日志不应出现依赖安装、Electron 下载、native addon rebuild、完整 main bundle rebuild 或全量 Rust rebuild。
- Chromium/WebKit、动态库和文件系统缓存造成的小幅首轮差异可以保留，但必须先排除工具链重建和固定等待。

## 性能验收

记录至少三次完整重启：

| 样本 | 从菜单点击到旧 PID 退出 | 到新 PID | 到可交互窗口 | 是否 rebuild |
| --- | ---: | ---: | ---: | --- |
| 第一次 |  |  |  |  |
| 第二次 |  |  |  |  |
| 第三次 |  |  |  |  |

满足以下条件后再交付：

- 第一次未因环境/命令差异触发额外构建。
- 第一次和热重启使用同一启动拓扑、runtime/Node/package-manager 版本、cwd 与稳定环境。
- 同一时刻只有一个 main process 和一个预期 dev server。
- 新窗口不是旧 renderer reload，且完成真实 PID 替换。
- `Cmd+Q` 后没有自动后继实例或遗留端口。
