# Changelog

## [0.6.1] - 2026-10-31

### Changed

- reload 后的分组校验额外比较 fixed 非空的 URLTest/Fallback 组（用户手动固定的节点）；未固定的 URLTest/Fallback 每次 reload 都会自动重选，不参与比较，避免误报。问题文案由 Selector choices changed 改为 Group choices changed
- SKILL.md 与 troubleshooting 补充：reload 前建立的连接会一直走旧链路直到断开，验证新规则只看 reload 后新出现的 /connections id，或先重启应用

## [0.6.0] - 2026-10-31

### Fixed

- direct-list --apply 在 Clash Verge Rev owner-scoped 服务模式下热加载失败：服务模式内核的 home 是 root 所有的 runtime 目录，按 path 热加载被 Mihomo 以 SAFE_PATHS 拒绝（HTTP 400）。现改为发送 payload（生成配置全文），并把其中的 external-controller-unix 固定为内核正在使用的 socket；其他模式仍按 path 热加载，被 SAFE_PATHS 拒绝时自动改走 payload
- 热加载失败不再只打印失败：reason 与 reload_attempts[].error 给出 Mihomo 原始报错（或无响应原因），已写入的文件自动还原并以退出码 2 结束，不再停在「已持久化、未生效」状态
- 热加载改用 60 秒超时，不再受控制接口默认 3 秒超时限制

### Added

- 热加载成功后用 wait_for_runtime 重新探测控制 socket，校验 /rules 中每个 host 都是精确 DOMAIN -> DIRECT，并确认所有 Selector 分组选择不变；任一不满足时 ok=false，问题列在 verification.issues，文件保持已保存
- apply 结果 JSON 新增 reload_attempts、restored_files、verification 字段，reason 始终存在（成功时为 null）
- troubleshooting 新增 SAFE_PATHS 400 与 Selector 选择变化两条排障映射
- 新增 mock 控制器测试：服务模式 payload 热加载与 socket 固定、sidecar 按 path、SAFE_PATHS 回退、报错透出与文件还原、无响应超时、Selector 选择变化

## [0.5.0] - 2026-10-25

### Added

- diagnose 按运行模式定位内核日志；读不到时输出 Recent logs: UNAVAILABLE 和每个位置的原因（JSON 计数为 null），不再静默输出 0
- 服务模式（socket 位于 clash-verge-service/users/<uid>/）只认 /Library/Application Support/clash-verge-service/users/<uid>/logs（Linux 为 /var/lib/...），不再回退到旧模式遗留的 data-dir 日志；其他模式在 logs/sidecar、service-logs/service、logs/service 中取最新一份，并显示来源与修改时间
- 新增 diagnose --live-logs SECONDS：经控制 socket 实时采样 Mihomo /logs 流，服务模式下无需 root 即可取得日志证据
- direct-list 共用同一日志发现逻辑；日志不可读时打印 UNAVAILABLE 和原因，JSON 新增 log_issues
- 新增日志发现、权限拒绝、流解析与实时采样测试

## [0.4.0] - 2026-10-25

### Added

- diagnose / direct-list 在 Clash Verge Rev 服务模式下自动找到 Mihomo 控制 socket；所有候选都连不上时报错退出，不再输出空的运行时状态
- socket 探测顺序：--socket → 运行中内核的 -ext-ctl-unix → clash-verge.yaml 的 external-controller-unix → /var/run/clash-verge-service/users/<uid>/verge-mihomo.sock → /tmp/verge/verge-mihomo.sock → <data-dir>/mihomo.sock；人类可读输出新增 Runtime socket 行
- fix-wechat / rollback 重启后按同一顺序重新探测运行时；fix-wechat 找不到运行时时返回 ok=false 和备份路径
- 修复 Unix socket 连接失败时未关闭文件描述符
- troubleshooting 新增排障映射：明文 HTTP 代理节点的 CONNECT 按 host 被 GFW 重置，附物理网卡无认证 CONNECT 判别法，处理方式为改用带加密 dialer-proxy 的中转节点
- 补充 frontmatter compatibility 字段；新增 socket 探测与报错测试

## [0.3.1] - 2026-09-25

### Added

- 合并本地未提交改动到上游 0.3.0 之上
- 本地改动：统一展示名为「Clash 网络医生」，保持调用 ID 与能力契约。

## [0.3.0] - 2026-08-24

### Added

- add the shared feedback-classification and approval-invalidation gate used by every LovStudio Skill

## 0.2.0 - 2026-07-29

- Added `direct-list` discovery from active connections and recent rotated service logs.
- Added reusable Mihomo rule-provider list export and online rule application.
- Preserved existing `prepend` entries when adding new DIRECT rules.
- Corrected the Clash Verge Rev service-log path used by diagnosis.

## 0.1.0 - 2026-07-13

- Extracted into an independent source repository.
- Kept compatible with the `skill-publisher/dev-skills` aggregate bundle.
