# Tauri 图标校准 · Tauri Icon Alignment · Skill Card

## Description

将 Tauri macOS Dock 图标按 alpha 可见外框与参考图标对齐，并把资源生成、开发二进制嵌入和最终 Dock 视觉验收分开证明。

## Owner

local skill maintainers。

## License / Terms

MIT。输入的品牌图形、截图与目标项目仍受其原始许可和隐私边界约束。

## Use Case

面向维护 Tauri 桌面应用的工程与设计团队。它处理“画布一样大但 Dock 看起来不一样大”“圆角缺失”和“新资源没有进入开发二进制”等问题。

## Deployment Geography

可在本地兼容 Agent 运行；真实 Dock 验收适用于 macOS。

## Requirements / Dependencies

- Python 3.8+
- `Pillow>=9.0`
- PyYAML
- 目标项目已有的 Tauri CLI
- 可读取的 Tauri 源码、生成图标和 debug build 输出

## Known Risks and Mitigations

- 画布尺寸不能说明视觉尺寸：以 alpha 包围盒和同一 Dock 状态截图为准。
- 方形 opaque 输入不会自动变成圆角设计：先修正 artwork，再归一化。
- 图标文件更新不代表原生进程更新：检查 Cargo watch，并以 `.icns` SHA-256 匹配构建输出。
- 自动隐藏、缩放和缓存可能改变呈现：只在相同 Dock 状态下比较，并明确记录证据缺口。

## References

- [Machine-readable card](skill-card.yaml)
- [Primary workflow](SKILL.md)
- [Tauri runtime reference](references/tauri-icon-runtime.md)
- [Atomic Skill composition map](references/skill-composition.md)
- [Real user case](cases/cases.json)

## Skill Output

输出 JSON 测量、归一化 PNG、Tauri 资源/构建嵌入证据和 Dock 验收记录。运行时结论分为 `resource_ready`、`runtime_embedded`、`dock_visually_verified`，不混淆状态。

## Skill Version

0.1.0

## Ethical Considerations

只处理用户放入任务范围的本地图标和构建产物；不上传图像、截图、代码或本地路径。默认新建输出，覆盖已有文件必须显式确认。

## LovStudio Evidence

### User Cases

见 [`cases/cases.json`](cases/cases.json)。首个真实案例记录了从资源调整到运行时嵌入验证的完整 Tauri Dock 校准链路。

### Dimension Map

`skill-card.yaml` 记录视觉外框、运行时一致性、安全输出和可复现性四个维度及其当前证据状态。

### Pricing Basis

见 [`pricing-card.yaml`](pricing-card.yaml)。免费版本提供本地工作流与验证器，不包含设计、发布或托管服务。

### Distribution

当前仅本地准备完成；任何远程目录、市场或付费渠道都尚未发布。
