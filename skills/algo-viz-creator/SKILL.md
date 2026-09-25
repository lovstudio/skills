---
name: lov-algo-viz-creator
description: >
  为算法、数据结构或信息流程生成「逐步演示」的可交互可视化。输入：算法名或
  概念描述（如“把 KMP 做成可视化”）。输出：自包含单文件 HTML，支持播放/暂停/
  逐帧/变速与键盘演示，每步附中文解说与伪代码高亮。
  触发语：做成可视化 / 算法图解 / 逐步演示 / step-by-step visualization /
  interactive algorithm demo。
license: MIT
depends_on:
  - lov-branding-consistency
metadata:
  author: skill-publisher
  version: "0.1.1"
  card_standard: lovstudio/skill-card/v1
  tags:
    - visualization
    - algorithm
    - presentation
    - html
    - education
  compatibility: "Portable Agent Skills format. Requires python3; no npm or build step."
  dependencies:
    - python3
---

# 算法演示台 · Algorithm Theater

把一个算法、数据结构或信息流程，变成一份可直接双击打开、逐步播放的交互图解
（单文件 HTML）。每一帧对应一次可见的状态变化，配有中文解说、伪代码高亮和
播放控制，适合讲课、汇报与自学演示。

产出的 HTML 不依赖任何外部 CDN 或构建工具，离线可开，双击即演示。

## Triggers

### Activate when

- “把 {算法} 做成可视化 / 图解 / 动画”
- “给 {数据结构/流程} 写一个逐步演示”
- “用可视化讲清楚 {KMP / 快速排序 / Dijkstra / 背包 / 爬楼梯 …}”
- “帮我画个演示稿（算法向）”
- “build a step-by-step visualization for {algorithm}”
- “make an interactive demo of {data structure / process}”
- “create an algorithm explainer animation”

### Do not activate when

- 只需要静态示意图、架构图、关系图（无逐步逻辑）→ 交给 `lov-bp-deck`、
  `lov-diagram` 或 `frontend-design`。
- 需要品牌级长文/文章配图 → 交给 `document-illustrator` / `baoyu-article-illustrator`。
- 把可视化嵌入现有 React 应用并需要状态管理 → 本项目风格：直接按
  `TraceDefinition` 数据模型写 TS 模块，复用应用的播放器，不使用本 Skill 的
  单文件 HTML 产物。

## User Profile (cross-session)

Every generated Skill is connected to the shared `user-profile/v1` contract in
`skill.yaml`. Read the shared user, brand, workspace, preferences, and this
Skill's `skills.<skill_id>` namespace at the start of every run. Keep the source
portable: resolved personal values belong in the shared profile, never here.

When the user directly states a durable preference or brand fact, persist it
through `scripts/profile_store.py` and report the saved profile path. Put
Skill-specific values under `records.<field>`; use `brand.<field>` or
`user.<field>` for shared values. Do not persist inferred secrets or credentials.
See `references/user-profile.md` for the complete contract.

## Skill Group Composition

Read `references/skill-composition.md` before deciding whether to invoke or
extend any adjacent capability. The record distinguishes optional upstream and
downstream handoffs from embedded Kit modules. Do not silently depend on a
sibling Skill that is not shipped with this source.

## Workflow (MANDATORY)

**You MUST follow these steps in order.**

### Step 0: Resolve skill root, dependencies, and runtime context

- Use `SKILL_DIR` if the environment provides it.
- Otherwise infer the installed skill directory from the current skill context.
- Verify every required local module, reference, script, and asset before work:
  - `scripts/validate_viz.py`（帧模型校验）
  - `scripts/build_viz.py`（模型 → HTML）
  - `assets/template.html`（演示引擎模板）
  - `references/step-model.md`（帧模型规范与示例）
- If a required resource is missing, name its expected relative path and stop
  before producing a partial result.

When running scripts manually:

```bash
export SKILL_DIR="/path/to/lov-algo-viz-creator"
```

Resolve `context.profile` on every invocation. The precedence is current request,
project context, Skill-specific profile records, shared preferences, shared
brand/user profile, then safe defaults. A direct user statement about a durable
preference or brand fact should be saved with `scripts/profile_store.py record`
using `--confirm`, followed by a concise saved-path report.

### Step 1: Understand the requested outcome

- 确定要可视化的对象：是算法、数据结构、还是业务/信息流程？
- 确定示例数据与目标观众（自学 / 讲课 / 汇报）。
- 明确交付位置：默认写入 `./output/`（按输出规范），用户指定路径则尊重用户。
- 若算法存在多种实现（递归/迭代、不同的启发式），先确认用哪一种，不要自己拍板
  造成返工；其余技术细节（布局、帧数、措辞）由你按本 Skill 原则自行决定。

### Step 1.5: Analyze nearby Skills before implementation

- Inspect related local and installed Skills by routing contract and concrete
  input/output, not by filename alone.
- Record upstream, core, downstream, overlap, and not-composed decisions in
  `references/skill-composition.md`.
- Keep sibling Skills optional and artifact-based. When stages require hard
  coupling for one outcome, create a self-contained Kit instead.

### Step 2: Model the algorithm as step frames

这是本 Skill 的核心。先把算法“翻译”成帧序列，再交给引擎渲染。

**逐帧建模的六个原则**（详见 `references/step-model.md`）：

1. **最小推进单元**：每一帧 = 一次可见的状态变化（一次比较、一次交换、一次
   访问、一次松弛、一次入栈…）。细粒度的机械操作合并成一帧，目标帧数 5–40。
2. **active vs settled**：`active` 是当前正在操作的元素（每帧 1–3 个，聚焦）；
   `settled` 是已经确定/完成/访问过的元素（单调累积，不再变回）。观众靠这两组
   颜色读进度。
3. **动态值用 `values`**：DP 表填的数值、最短距离、计数等“中间结果”放进
   `values`（node 布局是 `{节点id: 显示文本}`，bars 布局是数组快照）。
4. **一句话叙事**：每一帧的 `note` 用一句中文讲清楚“这一步在做什么 + 为什么”，
   引用具体数值/字符（“B 与 D 匹配，继续比较下一位”），不堆术语、不说空话。
5. **伪代码对齐**：`code` 写 4–8 行人类语言伪代码，`codeLine` 指向当前逻辑行，
   让观众知道“此刻对应哪一步”。
6. **首末帧收尾**：首帧解释输入与起点；末帧总结结果（“拓扑序列是 …”）。

**选择布局**：

- `sequence`：数组/序列/字符串（KMP、二分、斐波那契、Z 数组）
- `network`：图/树/流程/依赖（BFS、Dijkstra、拓扑、Trie、架构流程）
- `matrix`：二维 DP 表 / 距离矩阵（背包、LCS、Floyd–Warshall）
- `bars`：数值排序/比较类（冒泡、快速、堆排序）

按以下顺序产出：

1. 先写一份 `model.json`（完整 schema 与示例见 `references/step-model.md`），
   直接在算法上**真实跑一遍**，逐帧记录 active/settled/values，不要凭想象编帧。
2. 用 `scripts/validate_viz.py model.json` 校验（error 必须清零，warning 按
   `--strict` 收敛）。
3. 用 `scripts/build_viz.py model.json -o output/xxx.html` 生成独立 HTML。
4. 打开生成文件做一次“人肉走查”：叙事是否每一步都成立、帧序是否正确、
   布局是否遮挡。

### Step 3: Validate the deliverable

- 校验通过：`validate_viz.py` error=0。
- HTML 生成成功：`build_viz.py` 有明确输出路径，双击可打开。
- 内容走查：note 每句准确、codeLine 对齐、无遮挡、无 emoji（用内联 SVG 图标）。
- 报告：给出输出文件路径、帧数、布局、演示方式（空格播放、←/→ 逐帧）。

## Dependencies

- `python3`（运行 `validate_viz.py` / `build_viz.py`）。
- 无需 npm、无构建步骤、无外部 CDN。
- 产物为自包含 HTML，浏览器（现代 Chrome/Safari/Edge/Firefox）即可打开。
