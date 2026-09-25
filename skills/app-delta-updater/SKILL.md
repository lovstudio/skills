---
name: lov-app-delta-updater
description: >
  为 Tauri 与 Electron 桌面应用设计、实现并验证自动更新，区分签名完整包与真实增量包。Use when the user asks to add, fix, or verify app updates, or mentions 自动更新、delta updater、Sparkle、latest.json、appcast 或更新签名。
license: MIT
compatibility: >
  Tauri 2 or Electron desktop applications with a signed release channel. Python 3.8+ is required for the static audit; PyYAML is required only to validate this Skill source.
metadata:
  author: contributors
  version: "0.2.1"
  card_standard: lovstudio/skill-card/v1
  tags:
    - desktop-app
    - auto-update
    - tauri
    - electron
    - delta
  compatibility: "Tauri 2 or Electron desktop applications with a signed release channel. Python 3.8+ static audit; PyYAML only for source validation."
  dependencies: []
---

# 应用更新助手 · App Update Assistant

为桌面应用交付一条可恢复、可发布、可回读的更新链路。先识别框架真实能力，
再决定使用签名完整包、Sparkle delta 或其他差分产物；不把普通全量更新描述成增量更新。

## Triggers

### Activate when

- 用户说“给这个 Tauri/Electron App 加自动更新”“支持自动发现并安装新版”。
- 用户提到“增量更新”“检查更新一直转圈”“latest.json”“appcast”“Sparkle”或“更新签名”。
- The user asks to “add automatic updates”, “implement a delta updater”, or “verify the desktop update release”.

### Do not activate when

- 用户只要修改版本号、更新日志或下载页，不涉及应用内检查与安装。
- 用户要网页热更新、PWA 缓存刷新或移动端 OTA；这些属于对应平台的发布能力。
- 用户已经完成更新器，只要求执行一次全渠道正式发版；交给应用发布工作流。

## User Profile (cross-session)

运行前读取 `skill.yaml` 声明的 `user-profile/v1` 上下文。当前请求和项目配置优先，
其次才是本 Skill 的发布渠道、增量策略等长期记录。用户明确要求长期保存默认渠道或
回退策略时，通过 `scripts/profile_store.py` 写入 `skills.lov-app-delta-updater.records`；
推断值与签名秘密不持久化。

## Skill Group Composition

先读 `references/skill-composition.md`。本 Skill 拥有跨框架的更新契约与验收结果；
相邻的 Electron Sparkle、应用重启和 CI/CD Skills 只作为可选交接，不是隐藏依赖。

## Workflow (MANDATORY)

**You MUST follow these steps in order.**

### Step 0: Resolve context and detect the update surface

1. 读取本目录 `skill.yaml` 与 `references/release-verification.md`。
2. 从当前仓库识别框架、目标平台、安装包格式、现有更新器、公开更新源、签名责任方、
   发布渠道与回滚路径。
3. Tauri 项目读取 `references/platform-tauri.md`；Electron 项目读取
   `references/platform-electron.md`。混合仓库按实际交付的桌面壳分别处理。
4. 可先运行：

   ```bash
   python3 "$SKILL_DIR/scripts/audit_updater.py" PROJECT_ROOT
   ```

5. 仅当更新渠道、目标平台或完整包回退策略缺失且会改变用户可见结果时，使用
   `AskUserQuestion`（或当前宿主的等价提问机制）提出一个聚焦问题。不得询问、持久化或
   回显私钥、签名口令、token 或完整私人路径。

### Step 1: Establish an honest capability contract

- 将运行时拆为：检查、下载/暂存、安装交接、重启后验证四段状态。
- 只有产物确实依赖“源版本 → 目标版本”且下载的是差分字节时，才称为增量更新。
- Tauri 2 官方 updater 默认消费签名平台包；若项目没有独立差分后端，将其报告为
  “签名自动更新”，并把 delta 标记为后续能力。
- Electron macOS 只有在项目明确使用 Sparkle-compatible 包装、稳定签名和架构专属 appcast
  时承诺 Sparkle delta；不得把 Electron 原生或普通完整包更新误称为 Sparkle delta。其他平台
  按实际 updater/blockmap 能力分别报告。
- 除非用户明确要求 delta-only，否则完整包是允许的可靠回退，不应被静默描述为 delta。

### Step 2: Make checks bounded and recoverable

- 每个更新服务只保留一个进行中的检查或安装任务。
- 给检查与下载设置明确超时；调用栈支持 `AbortSignal` 时，将取消信号传到底层请求。
- 超时或 feed 错误后等待旧任务收敛，再开放重试；不得留下永久旋转状态。
- 自动检查失败保持克制，手动检查、下载或安装失败必须显示可重试入口。
- 错误界面提供复制按钮，诊断至少包含 `context_id`、阶段、当前版本、目标版本和脱敏错误。

### Step 3: Enforce artifact and release policy

- 更新元数据按操作系统、架构和安装器区分，URL、长度、摘要与签名对应同一最终产物。
- 先完成代码签名与公证，再生成 feed 或 manifest；禁止引用公证前字节。
- 发布流水线缺少签名更新产物或必需架构时直接拦截公开发布。
- Tauri 配置必须把运行时插件、capability、`createUpdaterArtifacts`、公钥、endpoint、
  `TAURI_SIGNING_PRIVATE_KEY`（加密私钥另配可选的
  `TAURI_SIGNING_PRIVATE_KEY_PASSWORD`）和完整 `latest.json` 生成链连在一起。
- Sparkle delta 必须标注源版本与目标版本；delta-only 遇到完整包回退时停止并显示手动安装路径。

### Step 4: Implement restrained product UI

- 启动后后台检查；仅在发现新版、用户手动检查或安装链路出错时打扰用户。
- 设置页提供当前版本、上次检查时间、检查/下载/重试/重启操作和安装进度。
- 界面使用项目既有语义色与组件，不泄露发布流水线、密钥或内部产品意图。
- 下载完成不等于更新完成；安装交接与重新启动必须是独立状态。

### Step 5: Coordinate install and restart

- 在应用清理完成后再交给原生更新器；异步安装助手确认接手前保持进程存活。
- Windows、macOS 与 Linux 的退出/重启语义分别按当前 updater API 实现。
- 安装失败保留重试或手动安装路径；不删除用户数据，也不覆盖可回滚安装包。
- 普通用户主动重启与更新安装重启分开实现，避免把 WebView reload 当成应用重启。

### Step 6: Validate the deliverable

- 为单飞检查、超时、无更新、新版可用、下载进度、签名/manifest 缺失、安装失败与重启补测试。
- 运行项目允许的类型检查、原生检查、测试与格式门禁；尊重仓库对正在运行 dev server 的限制。
- 按 `references/release-verification.md` 做公开资源和旧版到新版的真实回读。
- `audit_updater.py` 只能证明本地静态接线；它通过后仍必须完成公开 feed、签名产物与已安装
  旧版到新版的回读。
- 最终报告：更新后端、支持平台、全量/增量类型、更新源、验证过的产物、已安装版本证据，
  以及仍需下一次正式 release 才能闭环的条件。

## Dependencies

- 目标项目自己的 Tauri 或 Electron 构建工具、签名身份与发布权限。
- Python 3.8+ 仅用于可选静态审计脚本。
- Sparkle tooling 仅用于 Electron macOS 的真实 delta 路径。

## Runtime context (shared)

字段解析顺序为：当前请求、项目上下文、Skill 专属记录、个人 Preferences、共享 Profile、
通用默认值。缺少会改变用户可见结果的必填字段时只问一个聚焦问题；错误输出使用脱敏的
`context_id`，不输出私钥、token、完整私人路径或原始配置。
