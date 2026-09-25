# lov-skill-creator · Skill 信任审阅

> 来源：`SKILL.md` · 版本：`4.3.0` · 模型：`lovstudio/skill-logic/v1`

## 信任覆盖

- 激活示例：2；非触发示例：2。
- 运行步骤：8；显式条件规则：1。
- 已链接资源：10；缺失资源：0；引用展开深度：2。
- Kit 模块：0；命名管线：0。
- 有能力依据的步骤：6；有验收规则的步骤：3；真实案例产物：0。

## 内部运行流程

```mermaid
flowchart TB
  internal(["Skill 内部执行开始"])
  step_001["1. 判断产品形态"]
  internal --> step_001
  step_002["2. 判断实现与组合方式"]
  step_001 --> step_002
  step_003["2.5. 创建前分析相邻 Skill 组"]
  step_002 --> step_003
  step_004["3. 始终声明用户 Profile 契约"]
  step_003 --> step_004
  decision_004_01{"当用户直接说明要供后续会话使用的值时"}
  join_004_01(["继续"])
  step_004 --> decision_004_01
  action_004_01["运行生成的 scripts/profile_store.py record ... --confirm 命令，并报告规范保存路径；推断值只保留…"]
  decision_004_01 -- "是" --> action_004_01
  action_004_01 --> join_004_01
  decision_004_01 -- "否" --> join_004_01
  step_005["4. 规划内容"]
  join_004_01 --> step_005
  step_006["5. 在本地初始化"]
  step_005 --> step_006
  step_007["6. 实现"]
  step_006 --> step_007
  step_008["7. 验证并安装"]
  step_007 --> step_008
  deliver(["交付并报告证据"])
  step_008 --> deliver
  classDef entry fill:#e0f2fe,stroke:#0284c7,color:#0c4a6e;
  classDef decision fill:#fef3c7,stroke:#d97706,color:#78350f;
  classDef process fill:#ecfdf5,stroke:#059669,color:#064e3b;
  classDef terminal fill:#f3e8ff,stroke:#9333ea,color:#581c87;
  classDef inspectable fill:#ecfdf5,stroke:#176b57,color:#064e3b,stroke-width:2px;
  class internal entry;
  class deliver terminal;
  class step_001,step_002,step_003,step_004,step_005,step_006,step_007,step_008 inspectable;
  class decision_004_01 decision;
```

## 资源与依赖关系

```mermaid
flowchart LR
  controller["主控制器 SKILL.md"]
  resource_001["CHANGELOG.md 源文件"]
  resource_002["README.md 源文件"]
  resource_003["references/cloud-split.md 参考文档"]
  resource_004["references/migration.md 参考文档"]
  resource_005["references/skill-card-standard.md 参考文档"]
  resource_006["references/skill-composition.md 参考文档"]
  resource_007["references/skill-standard.md 参考文档"]
  resource_008["references/templates.md 参考文档"]
  resource_009["references/user-config.md 参考文档"]
  resource_010["references/user-profile.md 参考文档"]
  resource_011["scripts/init_skill.py 脚本"]
  resource_012["scripts/profile_store.py 脚本"]
  resource_013["scripts/test_profile_contract.py 脚本"]
  resource_014["scripts/validate_skill.py 脚本"]
  resource_015["skill.yaml 运行时清单"]
  controller -.-> resource_012
  controller -.-> resource_006
  controller -.-> resource_010
  controller -.-> resource_011
  controller -.-> resource_003
  controller -.-> resource_014
  controller -.-> resource_008
  controller -.-> resource_005
  controller -.-> resource_004
  controller -.-> resource_015
  resource_004 -.-> resource_014
  resource_008 -.-> resource_011
  resource_008 -.-> resource_010
  resource_008 -.-> resource_012
  resource_008 -.-> resource_014
  resource_008 -.-> resource_006
  resource_010 -.-> resource_012
  classDef source fill:#e0f2fe,stroke:#0284c7,color:#0c4a6e;
  classDef linked fill:#ecfdf5,stroke:#059669,color:#064e3b;
  classDef unlinked fill:#f8fafc,stroke:#94a3b8,color:#334155,stroke-dasharray: 4 3;
  classDef missing fill:#fee2e2,stroke:#dc2626,color:#7f1d1d;
  class controller source;
  class resource_003,resource_004,resource_005,resource_006,resource_008,resource_010,resource_011,resource_012,resource_014,resource_015 linked;
  class resource_001,resource_002,resource_007,resource_009,resource_013 unlinked;
```

## 可追溯逻辑

| 步骤 | 摘要 | 来源 |
| --- | --- | --- |
| 1. 判断产品形态 | 提问前先使用当前请求、记忆、代码库和已有示例判断。 | SKILL.md:82-99 |
| 2. 判断实现与组合方式 | 自动选择，并简要说明结果。 | SKILL.md:100-115 |
| 2.5. 创建前分析相邻 Skill 组 | 生成骨架前，检查本地 Skill 源目录和已安装 Skill。 | SKILL.md:116-139 |
| 3. 始终声明用户 Profile 契约 | 每个新 Skill 都要在 skill.yaml 中声明 user-profile/v1。 | SKILL.md:140-167 |
| 4. 规划内容 | 确定性操作放入 scripts/，实现为独立的 argparse 命令行工具。 | SKILL.md:168-184 |
| 5. 在本地初始化 | 单一 Skill。 | SKILL.md:185-234 |
| 6. 实现 | 把源文件写成面向 Agent 的指令，而不是当前对话的笔记。 | SKILL.md:235-256 |
| 7. 验证并安装 | python3 scripts/validate_skill.py . | SKILL.md:257-281 |

### 条件分支

| 条件 | 动作 | 来源 |
| --- | --- | --- |
| 当用户直接说明要供后续会话使用的值时 | 运行生成的 scripts/profile_store.py record ... --confirm 命令，并报告规范保存路径；推断值只保留在当前请求上下文。 | SKILL.md:160-163 |

### 外部适用边界

> 这部分属于宿主路由，不进入上方 Skill 内部运行图。
- ✅ 用户要“创建 skill”“封装成 skill”“生成 Skill Kit”或优化 Skill 生成机制。 (`SKILL.md:31`)
- ✅ 用户要求创建、生成骨架、验证或在本地安装 Agent Skill。 (`SKILL.md:32`)
- ⛔ 用户只是在调用现有 Skill 完成业务任务。 (`SKILL.md:36`)
- ⛔ 用户要发布远程仓库、上架目录、生成平台发行包或上传 Skill；交给 lov-skill-publisher。 (`SKILL.md:37`)

## 诊断

- `info` · `unlinked_packaged_files` · 以下打包文件未被 SKILL.md 或已链接文档引用：references/skill-standard.md, references/user-config.md, scripts/test_profile_contract.py

> 说明：报告区分源码声明、能力依据、验收规则和真实效果。静态完整度不能替代运行案例与结果回读。
