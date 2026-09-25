# Skill 能力组合

## Nearby Skills Inspected

创建前已读取下列相邻能力的 SKILL.md 和命名合同。

| 能力 | 实际职责 | 组合关系 |
| --- | --- | --- |
| lov-skill-creator | 创建可验证、可安装的 Skill，含基本命名要求 | 上游提供能力 brief，接收中英文名称和新 ID 建议 |
| lov-skill-optimizer | 审计、源码修改、版本维护、安装与目录检查，含基础命名审查 | 本 Skill 提供候选选择与整组命名判断；优化器负责授权后的落地 |
| lov-gen-project-name | 为普通项目提供名称、slug 与定位 | 相邻领域，不接管其项目命名职责 |
| lov-branding-consistency | 品牌、场景与信息可见性门禁 | 声明依赖，只验收名称和简介，不接管事实或发布 |
| lov-skill-publisher | 校验源码、定价、打包与指定渠道发布 | 接收已落实并验证的命名改动及明确发布范围 |

## Atomic Handoffs

1. 创建器或已有源码 → 本 Skill：能力 brief、真实工作流、稳定 ID、旧名与风格依据。
2. 本 Skill → 品牌审校：名称、简介、受众、相邻卡片、受保护专名；返回可见文案验收。
3. 本 Skill → 优化器：`skill-naming-review/v1` 清单、完整范围、证据与精确显示字段；
   优化器负责实际修改、版本策略与安装回读。没有修改请求时不调用写入阶段。
4. 优化器 → 发布器：通过校验的源码、清单、发布目标与授权；发布器负责渠道结果。

## Overlap Decisions

创建器和优化器保留基本命名门禁。本 Skill 专门负责候选选择、双语风格与批量决策，
不复制版本递增、目录镜像、定价或发布脚本。除品牌审校外，相邻 Skill 都是可选交接。

## Composition Decision

采用 Single Skill：单个起名、改名与批量审查共用能力证据、风格与结果合同。
离线审计只是结果的结构检查，不是独立业务阶段，不构成 Skill Kit。
