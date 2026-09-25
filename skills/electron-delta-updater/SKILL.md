---
name: lov-electron-delta-updater
description: >
  为 Electron 桌面应用设计、实现和验证增量自动更新，覆盖 macOS Sparkle、签名、appcast、发布产物与失败拦截。用户提到增量更新、Sparkle、检查更新、appcast、DMG 更新或 delta updater 时使用。
license: MIT
metadata:
  author: contributors
  version: "0.2.1"
  tags:
    - electron
    - auto-update
    - sparkle
    - delta
  compatibility: "Electron projects; macOS delta mode requires Sparkle-compatible packaging and signing."
  dependencies: []
---

# Electron 增量更新 · Electron Delta Updates

为现有 Electron 应用交付可验证的增量更新链路；以用户实际安装包、公开更新源和安装结果为准，而不是以 CI 成功为准。

## Triggers

### Activate when

- 用户说“给这个 Electron App 加增量自动更新”或“检查更新一直转圈”。
- 用户提到 macOS Sparkle、appcast、DMG、blockmap、签名、公证或 delta 更新包。
- User asks to “add a delta updater”, “ship Sparkle updates”, or “verify an Electron update release”.

### Do not activate when

- 用户只想修改版本号、更新日志或普通下载页；使用版本管理或发布工作流。
- 用户要做网页热更新、PWA 缓存更新或移动端 OTA；使用相应平台的更新机制。

## Workflow (MANDATORY)

**Follow these steps in order.**

### Step 0: Establish the update contract

- 确认目标平台、包格式、当前更新器、更新源、签名责任方、发布渠道和回滚预期。
- 只有在明确排除完整包时，才把 macOS delta-only 作为发布承诺。
- 将检查、下载/暂存、安装交接、重启后验证拆成四个状态。
- 处理 macOS Sparkle 时读取 `references/electron-macos-delta.md`；修改发布流水线前读取 `references/release-verification.md`。

### Step 1: Make checks bounded and recoverable

- 每个更新服务只保留一个进行中的检查。
- 将 `AbortSignal` 传入包含 appcast 请求在内的每一层网络调用。
- 超时后终止请求，等待旧更新状态和连接收敛，再允许后续重试。
- 配置更新器自己的网络会话，避免把开发者终端代理当作运行时配置。
- 每次超时、下载失败或 feed 格式错误后，界面都保留可重试状态。

### Step 2: Enforce the artifact policy

- 生成按架构区分的 feed 条目，并让每个 delta 对应明确的源版本和目标版本。
- 暂存前核对签名、长度、架构和 URL。
- delta-only 模式遇到完整包回退时停止当前链路，展示手动安装路径，避免静默下载更大的归档。
- 需要本地 feed 代理时，仅绑定 loopback，限制为已核验的 delta URL，保留 HTTP Range 行为，并确保资源 URL 以 `.delta` 结尾。

### Step 3: Coordinate install and restart

- 将应用清理完成后再交给原生更新器。
- 在确认异步安装交接前保持进程存活。
- 使用 `references/release-verification.md` 验证暂存更新和重启后的已安装版本。
- 普通的用户主动重启使用 `lov-electron-app-relaunch`。

### Step 4: Validate the deliverable

- 为单飞检查、超时终止、旧检查恢复、完整包回退拦截、feed 代理 Range 和异步安装交接补充测试。
- 执行项目适用的格式化、lint、类型检查、测试、打包、签名和公证门禁。
- 验证公开发布页以及 appcast、delta 资源的直接响应；对照最终产物的版本、摘要、大小、签名和公证状态。
- 报告更新后端、支持平台、核对过的 URL、已安装版本证据和任何手动安装条件。

## Runtime context

运行前读取同目录 `skill.yaml`，由宿主的 `skill-runtime` 按“当前请求、项目上下文、个人配置、品牌 Profile、安全默认值”的顺序注入，只使用 manifest 声明的字段。

- 缺少 `required: true` 字段时，按 `questions` 向用户提出一个聚焦问题；回答只用于本次运行，除非用户明确要求保存。
- Profile 只用于公开品牌事实；个人配置只用于决策，不自动写入产物或源码。
- 调试报错提供可复制的 `context_id`、字段路径和来源，不输出秘密、完整私人路径或原始内容。

## Dependencies

- An Electron project with a defined packaging and signing owner.
- Sparkle tooling only for macOS Sparkle paths.
---

## Runtime context (shared)

运行前读取本 Skill 包的 `skill.yaml`，由宿主提供 `skill-runtime/v1` 上下文。字段解析顺序为：当前请求、项目上下文、个人 Preferences、品牌 Profile、通用默认值。

- 只使用 Manifest 声明的字段；Profile 保存公开品牌事实，Preferences 保存个人工作偏好。
- `required: true` 字段缺失时，按 Manifest 的问题配置向用户提出一个聚焦问题；用户明确同意后再保存回答。
- 报错提供可复制的 `context_id`、字段路径与来源，诊断内容避开秘密、完整私人路径和原始配置。


## 通用反馈闭环

用户在 Skill 驱动任务中提出修改意见时，继续当前产物前必须执行：

1. 先判断意见是 `task-specific`（仅本次）还是 `reusable`（可跨任务复用）。
2. `task-specific` 只修改当前任务，不改 Skill。
3. `reusable` 先确定作用域：领域规则先更新对应 canonical Skill；适用于所有 Skill 的规则先更新共享规范。
4. 完成规则更新、版本、lint 与分发核验后，再把修改应用到当前任务。
5. `reusable` 修改会使此前的“确认”“继续”“发吧”失效；完成当前产物修改和回读后必须停下，等待用户下一步指示，不自动进入发布、提交或其他外部写入。
