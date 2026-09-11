# Changelog

## 0.3.0 — 2026-09-11

- 改为免费公开发布：移除加密交付适配（`src/` + `public/` 布局、占位说明与 `exec` 运行指引），
  恢复扁平 Skill 目录，源码公开在 `lovstudio/feedback-loop-skill`。
- 安装方式统一为 `npx lovstudio skills add feedback-loop`，无需登录与 Credits 兑换。
- 安装脚本保留内嵌托管块兜底，被单独复制或经工具执行时仍可用。

## 0.2.0 — 2026-09-11

- 转为加密付费交付：`src/` 为真源、`public/` 为占位与密文包；SKILL.md 增加加密运行说明
  （脚本经 `lovstudio-skill-helper exec` 运行，引用文件经 `decrypt` 读取），
  安装器内置托管块兜底，单文件 exec 场景不再依赖 `assets/`。
- 按调用模型收敛为单 Skill：删除 Skill Kit 结构与六个内嵌模块
  （sense、judge、ledger、tune、report、init）。
- 被动感知、落账与规则迭代由根 Prompt 的反馈与迭代规则加协议驱动，不经过 skill 路由；
  用户可见的主动入口（评价、回扫、复盘、接入）保留在唯一 `SKILL.md`。
- 判定红线、最小改动清单与账本操作并入 `references/protocol.md`；
  `scan_session.py` 上移到 `scripts/`。
- 目录条目从 7 条降为 1 条；卡片与用例合并为一份。

## 0.1.0 — 2026-09-11

- 建立反馈飞轮 Kit：被动情绪感知、主动 judge、追加式账本、最小作用域迭代、
  满意度报告与一键接入六个模块。
- 定义 `feedback-event/v1` 与 `feedback-outcome/v1` 两种记录、强度 1–5 标尺、
  作用域阶梯（task → skill → reference → root-prompt）与闭环状态机。
- 提供 `scripts/feedback_store.py`、`scripts/report.py`、
  `scripts/install_feedback_loop.py` 三个确定性 CLI。
- 输出自包含 HTML 报告：内联 SVG 趋势图，无外部字体、脚本或 CDN 依赖。
