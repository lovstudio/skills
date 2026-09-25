---
name: lov-skill-namer
description: >
  为单个或整组 Skill 起名、改名与审名；从真实能力和已认可范例出发，给出准确、简短、优雅、一致的中英文名称与命名清单。Use when naming a skill or reviewing a skill catalog's names.
license: MIT
compatibility: "支持 Agent Skills 的宿主；核心命名依靠语言判断。Python 3.8+ 用于离线清单审计与 Profile，PyYAML 用于源码校验。"
depends_on:
  - lov-branding-consistency
metadata:
  author: contributors
  version: "0.1.0"
  content_class: microcopy
  card_standard: lovstudio/skill-card/v1
  tags:
    - skill-naming
    - naming-review
    - bilingual-names
    - catalog-consistency
---

# Skill 命名大师 · Skill Naming Master

让 Skill 的名字说得清、记得住，放在同一组里也各有辨识度。

## Triggers

### Activate when

- “给这个 Skill 起个名字。”
- “这个 Skill 的中文名是不是不妥？”
- “所有 Skills 都参考这组风格，统一审查命名。”
- “Name this skill in Chinese and English.”
- “Review our skill catalog for concise, distinctive names.”

### Do not activate when

- 给公司、普通项目或 App 起名且不涉及 Skill；使用产品或项目命名能力。
- 创建业务实现、优化执行流程或修复脚本；使用 Skill 创建与优化能力。
- 仅改调用 ID、仓库名或目录；这是兼容性迁移，需要明确的迁移目标。
- 仅请求安装、发布、下架或同步官网；使用安装或发布能力。

组合请求按阶段处理：本 Skill 交付命名结果，已授权的修改和发布由相邻能力继续。
只问“名字是否合适”不构成修改或发布授权。

## Workflow

### 1. 读懂能力与范围

读取当前请求、`skill.yaml` 声明的 Profile 字段及
[能力组合](references/skill-composition.md)。从给定 SKILL.md、README、实际输出与
相邻 Skill 中提取：服务谁、接收什么、做什么、交付什么、明确不做什么。
名字和旧 description 都可能过时；实际工作流与可回读结果提供能力证据。

单个起名：输入足够就直接推荐；仅当用途无法查明时问一个用途问题。
批量审名：先列全范围和稳定标识，解析软链接与源目录；镜像和安装副本不是独立产品。
同一 ID 对应不同实现时标记待核实，保留两个来源，不猜谁是主版本。

### 2. 建立风格基准

读取 [命名判断](references/naming-style.md)。优先级为当前明确要求、项目限制、
用户认可名称、长期命名偏好、一般命名原则。

将已认可名称逐字锁定，中文与英文分别记录认可来源。参考任务只提供命名风格，
其中的发布、下架、账号操作不自动成为当前指令。包内案例不是其他用户的默认配置。
新请求明确推翻旧名称时记录新认可值及替代原因。

### 3. 提出或保留名字

按真实能力选取功能、结果、角色或意象表达，无需统一句法。
单个命名默认给一个最佳推荐，必要时加最多两个有实际差异的备选及一句理由。
批量任务逐项判断，包括保留项；不为提高改动数量强行改名。

中文读得顺、说得出，英文自然表达相同能力。作者或工作室前缀放到作者信息中；
GitHub、微信等帮助识别任务目标的平台名可以保留。大师、专家、神器、小能手等
可以使用，但必须适合能力与语气，不能给整组套同一个后缀。

### 4. 放回整组与实际界面审校

同时看名称、简介、核心工作流和相邻卡片，检查：

1. 是否承诺了实际没有的能力，或把子模块误叫成整个产品？
2. 能否读懂所属领域，是否有更短而不失辨识度的表达？
3. 是否保留已认可拼写、空格、大小写与风格？
4. 中英文是否重名、近似到难以区分，或把不同能力混成一个？
5. 是否与整组气质协调，又保留每项特点？

调用 `lov-branding-consistency` 对名称与一句话说明执行品牌语境验收。
用户认可专名按原文保护；不能拿通用文案规则否定“专业海报”等明确基准。
依赖不可用时报告未完成的门禁，不声称全套验收通过。

### 5. 输出命名结果

简短请求直接交付名字。批量、需要改文件或交给其他 Skill 时，按
[结果清单](references/review-contract.md) 输出 `skill-naming-review/v1` JSON，
再给表格：标识、原名、推荐名、保留或修改、简短理由。
用户认可与编辑建议分别记录，无法核实的条目用 `review`，不要伪造完成。

在本 Skill 根目录运行只读校验：

```bash
python3 scripts/audit_names.py /path/to/naming-review.json
```

脚本检查覆盖率、重复键、重复标识、重复名称、已认可名称漂移与决策状态；
它不能判断优雅程度、核验能力事实或验证修改与线上状态。

### 6. 按授权交接与回读

需要落地时交出清单、原始能力依据与明确目标字段；按
[修改与同步边界](references/apply-and-sync.md) 由优化或发布流程完成。
显示名调整默认保留 runtime ID、slug、仓库、路径、Profile key 与版本化协议。
只记录真正观察到的本地、目录、网页和安装状态；生成清单不是发布成功。

## Profile

每次运行按 [Profile 合同](references/user-profile.md) 读取声明字段。
`records.naming_style` 保存明确希望长期沿用的原则；`records.approved_names`
按稳定标识、语言、原文及来源记录认可值。只持久化直接陈述且要求跨任务沿用的偏好，
不保存猜测、私有案例或凭据。报告实际 Profile 路径；临时选择留在本次清单即可。

## Dependencies and validation

- `lov-branding-consistency`：最终短文案的受众与品牌门禁。
- 离线审计与 Profile：Python 3.8+ 标准库，无网络或凭据。
- 源码校验：Python 3.8+、PyYAML。
- 执行 `python3 scripts/validate_skill.py .`，再运行真实案例清单审计。
- 通过能力核对与编辑判断验收，不把字符数、脚本通过或自评分当作用户认可。
