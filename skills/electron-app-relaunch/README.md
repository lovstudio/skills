# sgc-electron-app-relaunch

![Version](https://img.shields.io/badge/version-0.1.0-CC785C)

为 Electron 应用建立可验证的完整重启机制。

## 本地安装

将目录链接到本地 Agent Skills 目录，链接名为 `sgc-electron-app-relaunch`。安装后可直接说“在菜单里加一个重启应用”。

## 使用

- “给这个 Electron App 加原生菜单的完整重启，并保留 renderer reload。”
- “开发态点击重启后打开了旧窗口，定位实际进程并修复启动参数。”

## 质量门

```bash
python3 scripts/validate_skill.py .
```

还需验证一次真实菜单点击后的替换进程。

## 依赖

- Python 3.8+
- PyYAML
- Electron

## License

MIT
