# 网页截图导出 · Web Capture Export · Skill Card

This human-readable card mirrors `skill-card.yaml`. It is a release record, not
an implementation note. A reviewer should understand the Skill without opening
its source.

## Description

给任意静态 HTML 网页注入一个自包含的 modern-screenshot 导出按钮，一键导出主体
内容为 PNG。核心保证：截图与浏览器实际渲染一致（文字不因容器宽度测量偏差而换行），
2x 分辨率适合网络传播。

## Owner

由 LovStudio contributors 通过本地 Skill 源维护。

## License / Terms

Skill 指令、脚本与注入模板按 MIT 复用；内联的 modern-screenshot 库按其自身 MIT
许可；目标页面保留其原有许可与第三方义务。

## Use Case

面向需要把 HTML 报表、数据看板、落地页等网页一键导出为分享图片的个人或团队。
页面已是静态 HTML，希望加一个导出按钮，点击即生成与屏幕一致的高分辨率 PNG。

## Deployment Geography

在本地运行，适用于任意静态 HTML 页面（file:// 或任意静态服务器），无地域限制。

## Requirements / Dependencies

- Python 3.8 或更新，仅用标准库。
- 端到端验证需 headless Chrome/Chromium。
- 无 Skill 凭据；modern-screenshot 内联，无 CDN 依赖。

## Known Risks and Mitigations

- 文字错误换行：显式传入 scrollWidth/Height，并用 headless Chrome 断言输出尺寸精确等于节点尺寸 × scale。
- 暗色页面白底/按钮不可读：背景取 body 计算色，按钮颜色用 var(--x, fallback) 适配主题。
- 第三方库体积/未知依赖：固定 modern-screenshot 版本并内联于 assets，离线可用。

## References

- [Machine-readable card](skill-card.yaml)
- [Primary Skill instructions](SKILL.md)
- [Integration contract](references/integration-contract.md)
- [Acceptance checklist](references/acceptance-checklist.md)

## Skill Output

输出是带导出按钮的 HTML（内联 JS/CSS）与端到端验证报告。调用方控制目标路径、
主体 selector、宽度、缩放与下载文件名。完成要求 headless Chrome 尺寸一致性断言
与验收清单逐项核对。

## Skill Version

0.1.0

## Ethical Considerations

不注入跟踪、不采集用户数据、不上传内容；截图仅在本机浏览器内完成。导出内容归属
目标页面作者，需遵守其版权与分享边界。

## LovStudio Evidence

### User Cases

[`cases/cases.json`](cases/cases.json) 记录了首个真实案例：给《手工川 DSH 剪辑成本
审计》HTML 加一键导出 PNG，端到端验证 `OK out=1520x2998 node=760x1499 expect=1520x2998`。
不宣称第三方生产页面上线。

### Dimension Map

- 渲染一致性：evidence 存在于脚本显式 width/height 与 verify 尺寸断言；无分数宣称。
- 传播分辨率：evidence 存在于 scale/--width 参数；无分数宣称。
- 可移植自包含：evidence 存在于内联库与 Library 小节；无分数宣称。
- 失败可诊断：evidence 存在于 .shot-err/#shot-err-copy 逻辑；无分数宣称。

### Pricing Basis

初始本地源免费，最大化复用并收集真实页面集成证据。不含目标页面制作、视觉设计、
远程发布与持续支持。

### Distribution

- WorkBuddy：未发布。
- SkillPay：未发布。
- GitHub：未发布。
- LovStudio：仅本地安装。
