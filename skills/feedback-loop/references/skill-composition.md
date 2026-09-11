# Skill Group Composition

## Nearby Skills Inspected

| Skill | 路由契约 | 关系 |
| --- | --- | --- |
| `lov-skill-creator` | 创建、验证、安装 Skill 与 Kit；内含任务反馈分层规则 | upstream：本 Skill 用它生成与校验自身 |
| `agent-self-reflection` | 定时自省，读取近期会话并写改进结论 | 邻近但不同：它分析 Agent 自身表现，不采集用户满意度、不做事件账本与统计 |
| `self-improving` | 记录纠正、维护分层记忆文件 | 邻近但不同：它沉淀长期偏好；本 Skill 记录单次反馈信号并统计趋势 |
| `lov-distill-to-system` | 把可复用经验写入项目或共享规范 | downstream：可复用反馈确认为规则后，可由它继续落库 |
| `lov-share-session` | 把会话导出为公开页面 | not composed：公开分享会引入隐私边界，反馈账本默认不外发 |

## Atomic Handoffs

- 主动入口：用户表达评价、要求回扫、要求复盘或要求接入时进入本 Skill。
- 自动链路：根 Prompt 的反馈与迭代规则读取 `references/protocol.md` 与
  `scripts/feedback_store.py`，不经过 skill 路由。
- 数据契约：`feedback-event/v1` 由评价入口或回扫判定产生，落盘与合并归账本脚本；
  `feedback-outcome/v1` 由闭环步骤回填；报告脚本只读消费两者。
- 接入脚本输出宿主写入计划与验证清单，不读写账本内容。
- 验收归属：落盘正确性属于账本脚本，规则改动有效性属于闭环步骤，统计口径属于报告脚本。

## Overlap Decisions

- 与 `agent-self-reflection` 保持分离：自省关注 Agent 自身可改进点，本 Skill 关注
  用户对结果的评价并保留统计口径；两者可以先后运行，但不互为依赖。
- 与 `self-improving` 保持分离：记忆写入属于长期偏好，反馈事件属于可统计信号；
  反馈被确认为长期偏好后，才由记忆能力另行写入。
- 不再保留独立的情绪分析、账本、迭代、报告与安装模块：它们没有独立于本闭环的
  用户结果，判定与操作规则并入协议后由根规则与唯一入口调用。

## Composition Decision

Single Skill。四条能力共享同一份协议、同一个账本与同一条闭环，属于同一个用户结果
（让 Agent 随反馈迭代），且自动链路不经过 skill 路由。
0.1.0 的 Kit 形态（控制器加六个内嵌模块）在 0.2.0 收敛：只有需要主动调用的入口
才保留在 Skill 层，其余作为协议与脚本存在。
