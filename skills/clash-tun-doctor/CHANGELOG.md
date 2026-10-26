# Changelog

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
