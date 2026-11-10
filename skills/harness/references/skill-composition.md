# Skill Group Composition

本记录写于创建时（2026-11-10），依据是各 Skill 的路由描述与实际输入输出，而不是名字。

## Nearby Skills Inspected

| Skill | 它实际接收与产出的东西 | 分类 | 结论 |
| --- | --- | --- | --- |
| `lov-skill-creator` | 需求 → 经校验并本地安装的 Skill 源码目录 | upstream atom | 它产出的源码目录和安装链接正是本 Skill 扫描的对象；本 Skill 不创建 Skill。 |
| `lov-skill-optimizer` | 一个或多个 Skill 源码路径 → 改写后的源码、统一的版本号与变更记录 | downstream atom | 本 Skill 发现版本不一致、描述过长等问题后，把源码路径交给它；本 Skill 不改写内容。 |
| `lov-skill-publisher` | 已校验的源码路径 → 远端仓库、目录条目与线上状态 | downstream atom | 源码领先目录、镜像缺失、没有远端时交给它；本 Skill 只读本地目录文件。 |
| `lov-skill-visualizer` | 单个 Skill 目录 → 这个 Skill 的内部流程图与信任审阅页 | not composed | 它解释一个 Skill 的内部；本 Skill 看的是全部 Skill 的安装与源码状态。 |
| `lov-agent-instructions` | 项目仓库 → 项目级指令文件的诊断与改写 | not composed | 它面向项目里的指令文件；本 Skill 面向用户级的根 Prompt 与宿主绑定，且不改写正文。 |
| `lov-distill-to-system` | 有证据的经验 → 写入项目或共享规则 | downstream atom | 规则引用失效路径、编号重复这类问题由它或用户编辑规则文件解决。 |
| `lov-harness-issue` | 产品问题或模糊需求 → 用户目标、验收标准与执行计划 | not composed | 只是名字相近。它处理产品需求，和本机 Agent 配置无关；两边的触发语里都写明了区分。 |
| `lov-skill-namer`、`lov-skill-pricing` | Skill 清单 → 命名建议；Skill → 定价卡 | not composed | 目录的展示名与付费标记在工作室页签里只读显示。 |
| `lov-feedback-loop` | 用户反馈 → 反馈事件与满意度报告 | not composed | 没有产物级的交接。 |
| `find-skills`、`skill-vetter` | 需求 → 可安装的第三方 Skill；待装 Skill → 安全审查 | not composed | 它们发生在安装之前；本 Skill 检查安装之后的状态。 |

另外检查了维护者本机已有的宿主链接同步脚本：它只为共享目录里的条目补建缺失的宿主链接。
本 Skill 的“安装到宿主”沿用它的命名规则（优先用 frontmatter 的 `name`），不取代它。

## Atomic Handoffs

```text
lov-skill-creator
  Skill 源码目录 + 共享目录里的安装链接
                |
                v
lov-harness（本 Skill）
  快照 JSON / Markdown 报告 / 驾驶舱 / 整理记录
        |                      |                       |
        v                      v                       v
lov-skill-optimizer      lov-skill-publisher     lov-distill-to-system
  源码路径 + 问题 ID       源码路径 + 目录差异      规则文件 + 问题 ID
```

交接物都是路径加问题 ID。本 Skill 的验收边界是：扫描结果与文件系统一致，整理计划按原样执行并
可以撤销。下游各自对改写后的源码、发布状态和规则正文负责。驾驶舱里的“复制指令”只把路径放进
一句不点名任何 Skill 的请求，由用户的 Agent 自行路由。

## Overlap Decisions

- **与 `lov-skill-optimizer` 的版本检查**：两边都会读各个版本号。本 Skill 只在全部源码范围内标出
  不一致，修复仍由它完成，所以保留为只读检查，不复制它的改写逻辑。
- **与 `lov-skill-creator` 的校验器**：驾驶舱的“运行校验”直接调用随本源码交付的同一份
  `scripts/validate_skill.py`，没有另写一套规则。
- **与本机链接同步脚本**：功能有交集（建立宿主链接），但它是批量补全，本 Skill 是逐项、可撤销的
  整理，并额外处理断链、绕经其他宿主的链接和停用。
- 没有发现拥有同一个用户结果的 Skill，因此新建而不是扩展已有 Skill。

## Composition Decision

`lov-harness` 是 **Single Skill**。规则、已装 Skill、工作室源码三块内容共享同一次本机扫描和同一份
快照，是同一个结果的三个视图，而不是各自带输入输出合同、需要按顺序串联的阶段，因此不做成
Skill Kit。扫描、驾驶舱服务与整理引擎都在 `scripts/harness.py` 一个文件里；界面资源在
`assets/dashboard/`。所有 sibling Skill 都是可选的下游交接，没有一个是运行依赖。
