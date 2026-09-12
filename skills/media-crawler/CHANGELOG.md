# Changelog

## [0.3.1] - 2026-09-12

### Fixed

- rename display name to 万能视频下载 / Universal Video Grabber
- 调用 ID lov-media-crawler、仓库名与配置键保持不变

## [0.3.0] - 2026-09-12

### Added

- 视频号新增「微信客户端取流」路径：`setup-wxclient` 下载并按官方 checksums 校验 `ltaoo/wx_channels_download` v260907，生成独立工作目录；`scripts/wxclient.sh` 提供 start/status/stop，启动需用户以管理员身份执行。
- `download --via {auto,yuanbao,wxclient}`：auto 在元宝解析失败且本地下载器在线时自动回退到微信客户端取流，通过 `/api/channels/feed/profile` 与 `/api/v1/download_task/create` 建任务并轮询到完成，沿用同一套媒体验证与报告。
- `probe`/`doctor` 报告本地下载器安装与在线状态；新增错误码 `wxclient_unavailable`、`wxclient_not_connected`、`wxclient_failed`。

### Changed

- 视频号解析：只有 HTTP 401/403 才报 `authorization_failed`；元宝鉴权通过但返回空 `wx_export_id` 时改报 `resolver_failed`，并说明是发布方限制或链接受限，避免误导用户反复重新授权。
- 授权脚本：登录态有效但测试链接本身不可解析时也保存凭据，并提示换一条公开链接验证。
- Frontmatter：`compatibility` 与 `depends_on: [lov-branding-consistency]` 提升到顶层；描述补充触发语；README 增加 `npx skills add lov-media-crawler -g -y`。
- 统一展示名为「媒体下载器」，保持调用 ID 与能力契约。

## [0.2.0] - 2026-08-24

### Added

- add the shared feedback-classification and approval-invalidation gate used by every LovStudio Skill

## 0.1.0

- Add a single-link resolver, resumable aria2/curl transfer and media verification report.
- Add one-time Tencent Yuanbao authorization with macOS Keychain storage for WeChat Channels.
- Add a pinned, license-gated MediaCrawler adapter for its seven open-source platforms.
- Verify a real MP4 transfer and the supplied WeChat Channels public-metadata boundary.
