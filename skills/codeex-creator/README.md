# Codeex 插件工坊 · Codeex Plugin Studio

![Version](https://img.shields.io/badge/version-0.2.1-CC785C)

为 Codeex 创建、验证和迭代独立运行时插件，并把源码落盘、安装状态、运行时激活和回滚拆成可审计的原子步骤。

## 安装

从包含本 Skill 的本地 checkout 安装：

```bash
npx skills add ./codeex-creator-skill --all -g
```

使用已有 Skill 管理器时，也可以把 canonical source 作为 symlink 安装；
运行时不依赖固定的用户目录。

## 用户 Profile（跨 session）

`skill.yaml` 声明 `user-profile/v1`。只有用户明确要求长期复用 Codeex 根目录时，才把它原子写入 `skills.lov-codeex-creator.records`；推断路径、token 与凭据不会保存。

## 使用

创建一个 renderer 插件：

```text
帮我创建一个 Codeex 插件，在插件目录中增加可独立开关的本地诊断面板。
```

输出包括插件目录、manifest、声明式 hook、权限说明、聚焦测试，以及安装、激活、卸载和回滚证据。

创建同时包含 renderer 和本地控制 API 的插件：

```bash
python3 scripts/codeex_plugin.py scaffold prompt-tools \
  --project-root "$CODEEX_ROOT" \
  --description "Expose prompt controls in the native composer." \
  --hook webview \
  --control-route
```

把现有功能插件化：

```text
Turn this Codeex launch modification into an independently installable plugin.
```

Skill 会先识别 `transformWebview`、`beforeLaunch` 与
`handleControlRequest` 边界，再把共享核心改动压缩到必要的稳定契约。

## 丝滑开发循环

- `transformWebview` / DOM / CSS：先跑浏览器 fixture，再重建 staged webview 和 runtime。
- `handleControlRequest` 或它导入的后端模块：先跑直接 API 测试，再重载 launcher/control service；仅重启 Electron 不算后端已更新。
- 原生 UI：先检查相邻控件的真实 DOM、SVG、尺寸和 computed color，能克隆就不近似重画。
- 生产回读：用 packaged runtime 的 CDP/DOM、真实 API、PID 和 active plugin set 证明结果。

完整矩阵见 [`references/development-loop.md`](references/development-loop.md)。

## 原子生命周期

- 新源码先写入同文件系统的 staging 目录，验证后原子重命名。
- 安装/卸载通过 Codeex CLI 更新 desired state，不手改状态文件。
- 每个有效插件都必须出现在 Codeex 管理页，并从管理页完成安装/卸载状态回读。
- `installed` 不等于 `active`；重启前后分别回读。
- 卸载只禁用插件，不删除源码或用户数据。
- 构建失败时保留当前运行版本，并通过反向状态变更回滚。

详见 [`references/atomic-lifecycle.md`](references/atomic-lifecycle.md)。

## 原子组合

[`references/skill-composition.md`](references/skill-composition.md) 区分 Codeex 运行时插件、Codex marketplace 插件、Lovinsp 集成和通用 Electron relaunch，避免同名“plugin”之间误路由。

## 可信度卡与用户案例

- `skill-card.yaml` / `skill-card.md` 记录用途、依赖、风险、输出与证据维度。
- `cases/cases.json` 指向真实的 lifecycle exercise 报告。
- `pricing-card.yaml` 记录免费边界和复评条件。

## 质量门

```bash
python3 scripts/validate_skill.py .
python3 scripts/codeex_plugin.py exercise daemonize --project-root "$CODEEX_ROOT"
```

## 依赖

- Python 3.8+
- Node.js 24+
- PyYAML 6+（仅 Skill 自检）
- 包含 Codeex 本地插件契约的仓库

## License

MIT
