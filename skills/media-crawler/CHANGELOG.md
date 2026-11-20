# Changelog

## [0.4.1] - 2026-11-20

### Fixed

- README 的安装命令改为 `npx lovstudio skills add media-crawler -g -y`：不带斜杠的名字会被 `npx skills add` 当作 git 源，报 repository does not exist，装不上。

## [0.4.0] - 2026-11-19

### Added

- 自建解析服务访问凭证：在当前进程设置 `LOV_MEDIA_CRAWLER_WORKER_CREDENTIAL` 后，`--worker-url` 的请求带 `Authorization: Bearer`（上游 `ltaoo/wx_channels_download` Worker 的约定）。凭证只发给 `--worker-url`，`--allow-public-resolver` 不会带上它；地址必须是 HTTPS（本机回环除外），否则报 `invalid_url` 且不发请求；重定向不重放凭证；凭证不进入 Profile、报告、错误信息或日志，也没有命令行参数。
- `doctor --json` 新增布尔字段 `environment_worker_credential`。

### Changed

- `resolver_unauthorized` 区分两种情况：未带凭证时提示设置 `LOV_MEDIA_CRAWLER_WORKER_CREDENTIAL`，已带凭证仍被拒时提示核对凭证。
- 离线用例增至 21 个，覆盖凭证只发给自建服务、不随重定向转发、不出现在任何输出里。

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
