# Changelog

## 0.1.0

- 首个版本：包装由 lov-cli2anything 生成的 Plane REST API v1 命令行，覆盖 130 个操作 / 17 个资源分组。
- 命令表在启动时由随包 `cli/openapi.json` 构建，Plane 升级后重新导出 schema 即可同步，无需改代码。
- 凭据只经环境变量或用户自有配置文件传入，不写入任何包内文件。
- 写操作要求先确认；创建工作项前先取状态与标签字典 id。
