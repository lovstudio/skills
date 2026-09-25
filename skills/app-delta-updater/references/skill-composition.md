# Skill Group Composition

## Nearby Skills Inspected

- `lov-electron-delta-updater`：拥有 Electron/Sparkle macOS delta 的专项契约，输入是 Electron
  项目与 appcast，输出是 Sparkle 更新链。与本 Skill 在 Electron 分支重叠，但覆盖面更窄。
- `lov-app-release`：输入是待发布应用与渠道，输出是已回读的全渠道版本；它消费本 Skill
  产出的更新配置与签名产物，不负责设计应用内更新状态机。
- `lov-release-via-cicd`：输入是仓库与发布目标，输出是 CI/CD 和 GitHub Release；它可执行
  更新产物发布，但不拥有全量/增量能力判定或运行时 UI。
- `lov-electron-app-relaunch`：输入是 Electron 生命周期需求，输出是可靠重启实现；只与普通
  重启相关，不替代更新安装交接。

## Atomic Handoffs

- 上游：版本管理或发布规划提供目标版本、渠道、平台矩阵和签名责任方；本 Skill 接收这些
  项目事实，不要求固定文件格式。
- 核心：本 Skill 输出运行时更新状态机、平台更新器配置、签名/feed 产物契约、发布拦截和
  验证报告；最终验收是旧版本能够发现、下载、安装并在重启后读取到目标版本。
- 下游：`lov-app-release` 或 CI/CD 发布能力接收已验证的构建/manifest 规则，执行正式发布并
  回传公开 URL、摘要、签名、公证和安装版本证据。
- 普通重启可把“用户主动重启”需求交给生命周期 Skill；更新安装重启仍由本 Skill验收。

## Overlap Decisions

Electron-only 项目仍可使用原 `lov-electron-delta-updater` 获得 Sparkle 专项深度；本 Skill
保留相同原则但不依赖它。Tauri 与跨框架请求由本 Skill 直接处理。应用发布和 CI/CD 保持
独立，因为“更新机制正确”与“某个版本已公开发布”是两个验收结果。

## Composition Decision

采用 Single Skill。平台检测、能力判定、运行时状态、产物策略和安装回读共同服务于一个
用户可见结果：应用可靠更新。Tauri/Electron 是互斥分支，不需要拆成硬耦合 Kit；平台细节
通过本 Skill 内部 references 渐进加载，外部 Skills 都是可选工件交接。
