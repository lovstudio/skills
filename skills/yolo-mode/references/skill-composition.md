# Skill Group Composition

## Nearby Skills Inspected

创建前读取了本地与安装目录中的实际入口，并检索了“无人值守 / unattended / autopilot / 自主执行”。

| Skill | 原有输入与输出 | 分类与决定 |
| --- | --- | --- |
| complete-the-mission | 明确目标 → 实现与验证；真实阻塞时仍可提问 | not composed；复用持续完成原则，但其结果是任务完成纪律，不拥有非交互模式 |
| lov-fix-until-no-error | 失败命令 → 修复与通过证据 | downstream atom；只有当前目标是修复时才交接验证命令与作用域 |
| lov-checkpoint | Git 差异与历史 → 里程碑记录，可在授权时提交 | downstream atom；需要正式项目存档时可交接本任务产物与验证记录 |
| automation-workflows | 重复业务流程 → 跨工具自动化方案 | not composed；不承担当前 Agent 会话的交互策略 |
| lov-branding-consistency | 用户可见说明 → 符合语境的说明 | 呈现依赖；只审校简报，不负责执行权限与目标验收 |
| lov-yolo-mode | 当前目标、预设、偏好、授权证据 → 非交互推进与可恢复交付 | core atom；拥有模式生命周期、session 权限准备、阻塞分支处理与诚实状态 |

## Atomic Handoffs

业务任务无需上述可选 Skill 也能执行。修复时交接原始失败命令、项目范围、已有授权与
成功标准；修复能力提供通过证据，本 Skill 负责非交互策略和总体状态。
正式存档时交接产物路径与验证结果，存档能力拥有记录验收；存档不自动授权 git commit。
已有业务 Skill 的可选提问遵循当前用户的无人值守指令，上位规则及业务授权边界不变。

## Overlap Decisions

complete-the-mission 允许阻塞时询问，修改它会影响并未要求无人值守的正常使用。
因此新增显式可启停的模式，不改它的默认行为。自动化服务、调度和防休眠不纳入本 Skill。

## Composition Decision

Single Skill，核心为 instruction-only。Profile 与校验脚本只是通用支持，不构成独立业务
阶段，不建立 Kit。相邻业务能力仅按制品可选交接；唯一声明依赖用于最终可见文本审校。

0.2.0 按用户明确请求将 lov-unattended 更名为 lov-yolo-mode，保持单 Skill。
新增权限预检与宿主正式允许接口的使用合同，不引入绕过权限的启动器。
