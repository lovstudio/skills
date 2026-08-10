# lov-electron-delta-updater

![Version](https://img.shields.io/badge/version-0.1.0-CC785C)

为 Electron 应用建立并验证可恢复的增量自动更新流程。

## 本地安装

将目录链接到本地 Agent Skills 目录，链接名为 `lov-electron-delta-updater`。安装后可直接说“给这个 Electron App 加增量自动更新”。

## 使用

- “为 macOS Electron 应用配置 Sparkle delta-only 更新，并验证 appcast 与公证产物。”
- “检查更新在代理网络下一直转圈，修复并验证后续重试。”

## 质量门

```bash
python3 scripts/validate_skill.py .
```

同时运行目标项目的更新器单测、打包、签名/公证和公开更新源验证。

## 依赖

- Python 3.8+
- PyYAML
- 目标 Electron 项目的打包与签名工具

## License

MIT
