---
name: lov-skill-distiller
description: >
  Use when 用户要将项目经验、故障复盘和已验证流程蒸馏为可创建的 Agent Skill 蓝图，明确用户结果、触发边界、私有信息边界与验收方式；触发词包括“把经验蒸馏成 skill”与 “distill experience into a skill”。
license: MIT
metadata:
  author: lovstudio
  version: "0.3.1"
  tags:
    - distillation
    - skill-blueprint
    - knowledge-productization
    - project-history
  compatibility: "Python 3.8+; git is optional for source-evidence collection."
  dependencies: []
---

# lov-skill-distiller — 将经验变成可创建的 Skill

这不是泛泛寻找机会，而是把已经发生过的工作蒸馏成稳定、可移植且可验收的能力契约。最终产物是 **Skill 蓝图**：它足以交给 `lov-skill-creator` 落地，却不泄漏人名、项目代号、私有路径、密钥或聊天背景。

## Triggers

### Activate when

- 用户说“把这段经验蒸馏成 Skill”“把 Yoda 的做法沉淀下来”或“把这次复盘做成可复用能力”。
- 用户提供项目历史、事故复盘、连续需求或真实交付，想从中抽出一项可复用 Skill。
- Use this when the user says “distill experience into a skill”, “turn this workflow into a reusable skill”, or “skill distillation”.

### Do not activate when

- 用户已明确要实现某一个 Skill：交给 `lov-skill-creator`。
- 用户要优化、修订或升级已有 Skill：交给 `lov-skill-optimizer`。
- 用户只要保存一条项目约定到系统提示词或项目说明：交给 `lov-distill-to-system`。

## Workflow (MANDATORY)

### Step 0: 选择待蒸馏的经验单元

以一个完整的“问题 → 判断 → 行动 → 验证”闭环为单位。优先选择经过真实运行、发布、安装或用户验收的经验；单次灵感、纯技术兴趣或只含内部背景的内容暂不提升为 Skill。

把人名、客户信息、项目代号、私有路径、访问凭据和临时聊天细节留在证据层，默认不进入蓝图的名称、描述和示例。

### Step 1: 收集原始证据（辅助，不是主产物）

针对仓库或材料创建可回看的证据摘要：

```bash
python3 "$SKILL_DIR/scripts/collect-source-evidence.py" PROJECT_PATH \
  --output skill-distillation-evidence.md
```

Git 历史只是线索。补充用户提供的复盘、验收记录、失败日志与行为变化；没有证据支撑的判断要标注为假设。

### Step 2: 蒸馏不变量

使用 [蒸馏透镜](references/distillation-lens.md)，从原始材料中抽出：

1. **用户真正要达成的结果**，而不是内部实现动作；
2. **稳定的判断顺序**：哪些步骤总是成立，哪些是可配置的变体；
3. **失败恢复与验收**：如何知道“真的成功”，而不是只看到提示、编译或静态检查；
4. **边界**：哪些输入不适用，哪些逻辑、数据或凭据需要保留为私有配置；
5. **最小复用单元**：应是 Single Skill、带确定性脚本的 Skill，还是由独立阶段组成的 Skill Kit。

不要把一次性动作逐条照抄成 Skill；合并同一用户结果下的不同渠道、模型、项目路径或工具实现。

### Step 3: 编写 Skill 蓝图

按 [Skill 蓝图模板](references/skill-blueprint.md) 交付一份中文蓝图。每份蓝图必须包含：

- 面向用户的名称与一句话承诺；
- 触发语句与至少一个明确的不触发场景；
- 输入、输出、核心流程与可配置项；
- 真实验收信号、常见失败与恢复路径；
- 私有信息边界；
- 一条或多条可回溯的证据摘要。

如有多个经验单元，按“同一结果是否共享上下文和验收”决定合并或拆分，最多推荐 3–7 个蓝图。

### Step 4: 做提升决策

对每项蓝图给出一个结论：

- **创建**：用户结果、边界、验收与证据均清楚；
- **继续蒸馏**：缺少真实验收、核心判断或可移植边界；
- **合并**：只是另一个渠道/参数/阶段，不该成为独立 Skill；
- **归档**：只能服务一次性项目上下文，保留为项目文档即可。

使用 [提升检查](references/distillation-lens.md#提升检查) 说明理由。分数只用于辅助排序，结论以可交付性为准。

### Step 5: 交接实现

用户选择“创建”的蓝图后，交给 `lov-skill-creator`：它负责实现、校验和本地安装。用户要求上架时，再交给 `lov-skill-publisher`。

## Dependencies

- Python 3.8+（仅标准库）
- Git（可选，用于仓库历史证据）
