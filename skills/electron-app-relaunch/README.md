# 桌面应用重启 · Desktop App Relaunch

![Version](https://img.shields.io/badge/version-0.3.1-CC785C)

为 Electron 或 Tauri 2 桌面应用建立可验证的完整重启机制，并稳定开发态第一次重启的性能。

## 本地安装

通过 Skill CLI 安装本地目录或 Git 来源：

```bash
export SKILL_SOURCE="/absolute/path/to/electron-app-relaunch-skill"
npx skills add "$SKILL_SOURCE"
```

也可以将 canonical 目录链接到 Agent Skills 目录，链接名保持 `lov-electron-app-relaunch`。安装后可直接说“在菜单里加一个重启应用”。

## 使用

- “给这个 Electron App 加原生菜单的完整重启，并保留 renderer reload。”
- “这个 Tauri App 的 `request_restart` 会让开发服务器一起退出，按真实 owner 修复。”
- “开发态点击重启后打开了旧窗口，定位实际进程并修复启动参数。”
- “第一次重启很慢、后面很快，找出构建环境或进程树差异。”
- “Cmd+Q 后 App 被 watcher 自动拉起，修复退出意图。”

## 质量门

```bash
python3 scripts/validate_skill.py .
```

还需验证真实菜单点击后的替换进程，分别记录第一次和至少两次热重启，并执行一次 `Cmd+Q` 残留检查。

## 依赖

- Python 3.8+
- PyYAML
- Electron main process 或 Tauri 2 Rust App core

## License

MIT
