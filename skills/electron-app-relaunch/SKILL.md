---
name: lov-electron-app-relaunch
description: >
  为 Electron 桌面应用实现并验证完整重启，区分 renderer 刷新、用户主动重启、开发态重启和更新安装交接。用户提到重启 App、菜单重启、Cmd+R、app.relaunch 或 restart Electron 时使用。
license: MIT
metadata:
  author: lovstudio
  version: "0.2.0"
  tags:
    - electron
    - relaunch
    - lifecycle
    - desktop
  compatibility: "Electron main-process applications in development or packaged production mode."
  dependencies: []
---

# Electron 应用重启

为用户提供真正重启桌面应用的入口，并在开发态、生产态和更新安装时保持正确的进程生命周期。

## Triggers

### Activate when

- 用户说“在菜单里增加重启 App”“实现重启 Yoda”或“完整重启 Electron”。
- 用户把 `Cmd+R`、reload、relaunch、退出再打开混在一起，需要修复实际行为。
- User asks to “restart the app from a menu”, “use app.relaunch”, or “make Electron dev restart reliable”.

### Do not activate when

- 用户只需要刷新页面或恢复某个 renderer 错误边界；使用 renderer reload。
- 用户要重启某一条 Agent/终端会话；使用会话生命周期或 PTY 工作流。

## Workflow (MANDATORY)

**You MUST follow these steps in order.**

### Step 0: Name the intended action

- Map every proposed UI entry to exactly one intent: renderer reload, full app relaunch, or update installation handoff.
- Do not bind a standard reload shortcut to full relaunch by accident. In Electron, the built-in View reload role commonly owns `Cmd+R` / `Ctrl+R`.
- Read [references/relaunch-contract.md](references/relaunch-contract.md) before implementation.

### Step 1: Centralize the relaunch path

- Put full-app restart in one main-process function, then invoke it from the native menu or typed IPC.
- In packaged production, call `app.relaunch()` followed by `app.quit()`.
- In development, relaunch the actual dev entrypoint with the Node executable and arguments that started the app; do not assume a packaged executable exists.
- Keep renderer reload separate and label it accordingly in the UI.

### Step 2: Preserve process ownership

- Let main-process shutdown hooks complete according to the product's session policy.
- Do not use the ordinary relaunch function to install an update. The updater must take control only after cleanup and staging have completed.
- When child processes, PTYs, local servers, or single-instance locks exist, define whether each survives, shuts down, or is reattached after restart.

### Step 3: Verify the real instance

- Add focused tests for the dev command construction and production relaunch path.
- Run the app, record its PID, executable path, working directory, and start time.
- Trigger the native menu item once, then confirm a replacement instance is running with a newer start time and the intended executable.
- Do not accept bundle text, menu existence, renderer reload, or a successful build as proof of full restart.

## Dependencies

- Electron main-process access to `app` and the target project's development command.
