# Changelog

## [0.3.2] - 2026-11-19

### Fixed

- 视频号解析：本机元宝凭据被拒（HTTP 401/403）且本次显式传了 `--worker-url` 或 `--allow-public-resolver` 时，回退到该解析服务，成功的报告带 `fallback_from: authorization_failed`；未传这两个参数时仍报 `authorization_failed` 并提示重新授权。回退不删除、不改写钥匙串条目，也不把 Cookie 发给解析服务。
- 解析服务自身返回 401/403 时改报新错误码 `resolver_unauthorized`，文案说明是解析服务拒绝访问，`next_action` 不再指向重新授权元宝；`--via auto` 在该错误下同样可回退到微信客户端取流。
- `authorize_yuanbao.py`：提示改为立即输出（后台运行时不再等到进程退出才出现），默认等待从 300 秒调到 600 秒，提示与超时信息写明可用 `--timeout` 调整。

### Changed

- 文档按 2026-11-19 实测更新：公共解析服务 `sph.litao.workers.dev` 返回 `401 {"error":"unauthorized"}`，上游 Worker 要求部署者配置的访问凭证，不再把它描述成可用路径。
- 新增 `tests/test_resolver_fallback.py`：13 个离线用例，用假的 `urlopen` 覆盖凭据回退与解析服务拒绝访问，不访问网络、不读钥匙串。

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
