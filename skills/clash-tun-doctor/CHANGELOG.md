# Changelog

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
