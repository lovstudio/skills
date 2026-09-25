# Atom Feature Dashboard

Dashboard 是真实控制面，不是展示型项目列表。默认信息结构：

1. **Atom index**：Feature 名称、总体状态、适用 surface、最后验证时间和阻塞项；
2. **Contract**：输入、输出、错误、权限、副作用、schema 版本和迁移状态；
3. **Run**：选择 surface、Profile Preset 与测试向量，编辑显式覆盖参数并执行；
4. **Compare**：并排显示规范化结果、副作用和允许差异；
5. **Evidence**：测试、构建、运行、部署和渠道回读，明确证据层级；
6. **Operations**：Docs、测试、SEO、GEO、Auth、支付、分析和支持状态；
7. **Logs**：可过滤的 request / run 记录，默认隐藏秘密与个人数据。

## Companion Workbench

本 Skill 必须随源提供可运行 Dashboard，而不只是一份界面规范。默认实现位于 `dashboard/`，
由 `scripts/atom_dashboard.py` 通过 loopback HTTP 提供静态前端和受限项目 bridge。它采用
ADE 的核心交互模型：工作区而非文件是组织单位，Agent、计划、运行、预览和 Review 在同一
窗口内完成；在本产品中，工作区进一步限定为 atom feature。

首版不内置代码编辑器或模型供应商。它负责组织、运行、比较和验收，并生成当前上下文的
Agent brief；具体 Agent 继续由 Codex、Claude Code 或其他宿主运行，目标项目工具链保持真源。

## Interaction rules

- 切换 surface 不丢失同一测试向量，只改变 adapter；
- 切换 Profile 时显示哪些参数来自 Preset、哪些来自当前显式覆盖；
- 无法执行的 surface 显示真实原因和下一步，不使用禁用按钮加模糊 tooltip；
- 状态标签使用 `planned`、`implemented`、`verified`、`released`、`not-applicable`；
- 危险或付费操作在执行前明确对象、费用和副作用；只读调试默认无需二次确认。

## Visual baseline

复用目标项目 semantic tokens。LovStudio 产品使用 Warm Academic：暖色画布、衬线标题、
无衬线正文、少阴影、柔和圆角；代码中使用 `bg-background`、`text-foreground`、
`bg-primary`、`border-border` 等 semantic class，不硬编码品牌颜色，不使用 Unicode emoji。

## Runtime boundary

Web Dashboard 只调用已有 API 或本地 dev bridge，不把秘密暴露到浏览器。桌面项目可通过原生
命令访问本地制品，但一次性运行、打开文件和终端交互保持命令式；服务端状态使用项目已有的
查询层与稳定 query key。

Bundled bridge 额外遵守：默认只读、只绑定 loopback 并校验本地 `Host`、只执行 manifest 中的 argv 数组、使用
`shell=False`、限制运行时长与输出长度、遮蔽常见秘密。允许执行和保存 Preset 分别由
`--allow-run` 与 `--allow-write` 显式开启。
