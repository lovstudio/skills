# lov-install-ai

![Version](https://img.shields.io/badge/version-0.1.0-CC785C)

为 App 快速加入可上线的 AI 功能，并在本地 Agent Client、MaaS 和混合模式之间选择合适通道。

## 本地安装

将目录链接到本地 Agent Skills 目录，链接名为 `lov-install-ai`。首次执行会从当前项目和共享 profile 推断模型偏好；显式项目需求覆盖已保存偏好。

## 使用

- “给这个桌面 App 加文件总结，用本地 Agent Client 优先，缺失时走 MaaS，并提供结果面板。”
- “给这个 Web App 加 AI 改写功能，走 MaaS，偏好快速模型，不显示模型选择器。”

## 质量门

```bash
python3 scripts/validate_skill.py .
```

还需完成一次真实用户操作、MaaS 失败路径和 Agent Client 缺失路径验证。

## 依赖

- Python 3.8+
- PyYAML
- 目标 App 的服务端或桌面本地适配层

## License

MIT
