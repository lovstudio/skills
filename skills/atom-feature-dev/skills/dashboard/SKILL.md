---
name: lov-atom-dashboard
description: >
  构建 Atom Feature Dashboard，读取真实 manifest、Profile、surface 运行结果与运营证据，支持切换、执行和结果对比。触发：“做 feature dashboard”或 “build an atom feature control panel”。
license: MIT
compatibility: "Portable Agent Skills format. Integrates with the target project's frontend, API or desktop bridge."
depends_on:
  - lov-branding-consistency
metadata:
  author: LovStudio
  version: "0.2.2"
  card_standard: lovstudio/skill-card/v1
  content_class: microcopy
  tags:
    - atom-feature
    - dashboard
    - debugging
    - evidence
    - profile
---

# 功能控制台 · Feature Dashboard

提供以 atom 为单位的生产、分发、调试与运营控制面。根 Skill 已内置可运行 Companion
Workbench；状态来自 manifest、测试报告和真实运行回读，不能用 UI 常量或构建成功伪造
verified / released。

## Triggers

### Activate when

- “做一个能切换 SDK、CLI、API、UI 和 Agent 的 feature dashboard。”
- “在面板里选择 Profile，运行同一测试并比较结果。”
- “Build an atom feature control panel with real evidence.”

### Do not activate when

- 只要通用管理后台、监控大盘或静态项目列表，不需要 atom contract 与跨 surface 调试。

## Workflow (MANDATORY)

1. 读取根 `references/dashboard-spec.md`、`dashboard/README.md`、manifest、目标 UI 规范和
   现有运行/查询边界。
2. 建立 atom index 与详情页：Contract、Run、Compare、Evidence、Operations、Logs。
3. Run 面板固定测试向量，允许切换 surface 与 Profile，并显示每个参数的来源和显式覆盖。
4. Compare 规范化结果、错误和副作用；时间戳、request ID 与展示包装不得造成伪差异。
5. Evidence 区分 planned、implemented、verified、released 和 not-applicable，链接到真实制品。
6. Web 端不读取秘密或本地任意文件；通过已有 API 或受限 desktop bridge 执行。
7. 使用 semantic tokens、键盘可达组件、移动端布局和清楚的失败/付费/危险操作文案。
8. 新项目优先直接使用根 Skill 的 `scripts/atom_dashboard.py` 与 `dashboard/`；目标已有产品
   Dashboard 时复用数据契约并在真实页面集成，不创建第二个控制面。
9. 完成静态检查后，从真实入口运行 golden、失败和 Profile 切换路径并回读状态。
10. 直接打开静态入口时只提供明确标注的只读 Demo；真实项目读写与运行只允许走本地 bridge。

## Output Contract

返回可运行 Dashboard route、loopback bridge、数据 adapter、主要组件、可执行 surface、
状态来源、运行证据和未支持项。没有真实运行证据时最多标为 `implemented`。

## Dependencies

Python 3.8+ 可直接运行内置 Companion Workbench；集成到目标产品时使用其 UI 栈、Atom
manifest、Profile resolver 与适用 surface 的受限执行接口。
