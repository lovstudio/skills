# 应用更新助手 · App Update Assistant · Skill Card

## Description

为 Tauri 与 Electron 桌面应用实现可靠自动更新，并清楚说明完整包、blockmap 与真实 delta 的能力边界。

## Owner

Lovstudio.AI，联系入口：https://lovstudio.ai

## License / Terms

MIT。Skill 可使用、修改和再分发；目标项目的签名证书、账号与平台条款由使用者管理。

## Use Case

适用于新增或修复应用内检查、下载、安装、重启与更新发布产物链路的桌面应用团队。

## Deployment Geography

全球；在本地仓库、CI/CD 与正式签名安装包中使用。

## Requirements / Dependencies

目标项目的 Tauri 2 或 Electron 工具链。静态审计需要 Python 3.8+；正式发布使用项目自己的签名与公证凭据。

## Known Risks and Mitigations

- 完整包被误称为 delta：以源版本、目标版本和实际差分字节为判定条件。
- manifest 指向错误产物：签名/公证后生成，并对平台、架构、长度、摘要和签名做发布拦截。
- 网络或安装卡死：使用单飞、超时/取消、重试状态与可复制诊断。

## References

- [Machine-readable card](skill-card.yaml)
- [Primary Skill instructions](SKILL.md)
- [Tauri platform contract](references/platform-tauri.md)
- [Electron platform contract](references/platform-electron.md)

## Skill Output

输出源码与配置修改、更新状态机、签名 feed/manifest 契约、静态审计结果和旧版到新版安装回读报告。

## Skill Version

0.2.0

## Ethical Considerations

不读取或输出私钥、token 和完整私人路径；不把 CI 成功、上传完成或下载 100% 描述成用户已安装。

## LovStudio Evidence

### User Cases

[`cases/cases.json`](cases/cases.json) 记录 Ataru Tauri 2 自动更新的真实实现与验证结果。

### Dimension Map

维度包括能力真实性、运行时恢复性和发布可验证性；证据见 `skill-card.yaml`，暂不使用缺乏跨项目样本的数值评分。

### Pricing Basis

当前免费，边界与复评条件见 [`pricing-card.yaml`](pricing-card.yaml)。

### Distribution

`workbuddy`、`skillpay`、`github` 与 `lovstudio` 当前均为 `not-published`；本次只完成本地安装与验证。
