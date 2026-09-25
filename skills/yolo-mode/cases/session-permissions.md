# 当前 session 权限证据与权限准备演练

版本 0.2.0，2026-09-07。

## 真实 session 证据

来源是本次宿主实时注入的权限声明，不是全局配置文件或命令成功的推断：

- sandbox_mode：danger-full-access；文件系统无限制。
- approval policy：never；当前 exec 不允许传入 sandbox_permissions 覆盖值。
- network access：enabled。
- 当前任务所需能力：本地 Skill 文件读写、Python 校验、安装符号链接与 Profile 写入。
- 判定：already_ready，本任务无需进一步启用权限。
- 实际动作：使用现有文件与命令权限完成更名和校验；没有修改当前 session 权限设置。

当前可用工具目录未提供 session 级权限切换或 YOLO setter。工具目录有应用权限工具，
但它们不负责 session 权限，当前任务也不需要第三方应用；未开启无关应用权限。
因此没有声称调用过切换接口，也没有声称所有第三方应用、OAuth 或系统隐私权限已开启。

## 人工语义演练

以下为规则演练，未实际变更其他 session：

| 情况 | 规则执行结果 |
| --- | --- |
| /lov-yolo-mode，当前权限已满足 | already_ready，直接继续，无重复确认 |
| 用户授权范围内，宿主正式接口允许设置必要权限 | 设置并回读后才记 configured |
| 写了全局配置，当前 session 未回读生效 | 不判定 configured |
| 只有应用权限接口，没有 session setter | 不借用应用接口伪造切换；记录 unsupported |
| 任务不使用某应用，但它尚未开启写权限 | 不开启无关应用权限 |
| 宿主强制 sandbox 或审批策略禁止改变 | 不绕过，完成可执行准备并继续独立分支 |
| 暂停模式时，本轮改变过临时 session 设置 | 在宿主支持且安全时恢复自己的变更，保留原有权限 |

这些演练不证明未提供接口的宿主支持热切换，也不是跨宿主实测。
