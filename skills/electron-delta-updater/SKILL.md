---
name: lov-electron-delta-updater
description: >
  为 Electron 桌面应用设计、实现和验证增量自动更新，覆盖 macOS Sparkle、签名、appcast、发布产物与失败拦截。用户提到增量更新、Sparkle、检查更新、appcast、DMG 更新或 delta updater 时使用。
license: MIT
metadata:
  author: lovstudio
  version: "0.1.1"
  tags:
    - electron
    - auto-update
    - sparkle
    - delta
  compatibility: "Electron projects; macOS delta mode requires Sparkle-compatible packaging and signing."
  dependencies: []
---

# Electron 增量自动更新

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

**You MUST follow these steps in order.**

### Step 0: Establish the update contract

- Identify target platforms, package format, current updater library, update feed, signing owner, release channel, and rollback expectation.
- Treat macOS delta-only behavior as an explicit product promise only when complete archives are intentionally excluded.
- Separate four states: check, download/stage, install handoff, and post-restart verification.
- Read [references/electron-macos-delta.md](references/electron-macos-delta.md) for macOS Sparkle work and [references/release-verification.md](references/release-verification.md) before modifying a release pipeline.

### Step 1: Make checks bounded and recoverable

- Use one in-flight check per update service.
- Pass an `AbortSignal` through every network layer, including appcast fetches.
- On timeout, abort the request, wait for stale updater state and connections to settle, then allow a later retry.
- Configure the updater's own network session; do not assume it inherits a developer shell proxy.
- Keep the UI state retryable after every timeout, download failure, or malformed feed.

### Step 2: Enforce the artifact policy

- Generate architecture-specific feed entries and match each delta to its source and target version.
- Verify signature, length, architecture, and URL before staging an update.
- In delta-only mode, stop on any complete-package fallback; surface a manual-install path instead of silently downloading a larger archive.
- If a local feed proxy is required, bind it to loopback, permit only the verified delta URL, preserve HTTP range behavior, and keep the served artifact URL ending in `.delta`.

### Step 3: Coordinate install and restart

- Complete application cleanup before giving control to the native updater.
- Keep the process alive until asynchronous install handoff is confirmed.
- Use [references/release-verification.md](references/release-verification.md) to verify the staged update and the installed version after relaunch.
- For a normal user-invoked app restart without an update, use `lov-electron-app-relaunch` instead.

### Step 4: Validate the deliverable

- Add tests for single-flight checks, timeout abort, stale-check recovery, rejected full fallback, feed proxy ranges, and asynchronous install handoff.
- Run the project's format, lint, typecheck, test, package, signing, and notarization checks that apply.
- Verify the public release page plus direct appcast and delta asset responses; compare the final artifact's version, digest, size, signature, and notarization state.
- Report the updater backend, supported platforms, checked URLs, installed-version proof, and any manual-install condition.

## Dependencies

- An Electron project with a defined packaging and signing owner.
- Sparkle tooling only for macOS Sparkle paths.
