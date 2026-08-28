# Skill Pricing Card：clean-mac

| 项目 | 结论 |
| --- | --- |
| 版本 / 交付单元 | 0.4.0 / 公开 Skill 源码与当前版本说明 |
| 目标买家 | 需要释放 macOS 空间，同时不能误伤活跃工程和应用工作区的个人与小团队 |
| 建议价格 | 139 Credits / 一次性解锁 |
| 稳定价格带 | 139 Credits |
| 首发测试价 | 139 Credits，首发 30 天或 100 次付费兑换后复评 |
| 渠道 | LovStudio 官网 Skill Publisher |
| 置信度 | case-backed |

## 为什么是这个价格

- 成本底线：按 18–28 小时需求、实现、测试和文档，加上未来 6 个月 6–10 小时维护与支持准备估算；直接基础设施成本接近零，主要成本来自持续适配 macOS、应用工作区与回滚边界。
- 价值锚点：本次真实运行将 `/System/Volumes/Data` 可用空间从阶段基线 23.19 GB 提升到 196.54 GB，净增约 173.35 GB，同时保留 Screen Studio 等受保护工作区；一次处理通常还能节省 30 分钟至半天的容量诊断、候选判断、迁移和异常恢复时间。
- 价格位置：139 Credits 是一次性公开源码交付的低门槛测试价。它显著低于单次安全清理的结果价值，用于验证付费意愿，不承诺人工代清理、托管执行或无限支持。

## 六维评分

| 维度 | 分数 / 5 | 权重 | 加分事实 | 扣分事实 |
| --- | ---: | ---: | --- | --- |
| 实际结果价值 | 4.5 | 30% | 可回读真实容量、迁移链接和回滚状态；避免误伤有直接价值 | 不同机器可释放空间差异较大 |
| 稀缺性与替代难度 | 3.5 | 20% | 把容量目标、分类、事务迁移、保护边界与验收串成完整流程 | 常见缓存清理工具可覆盖部分低风险场景 |
| 质量证据与购买信心 | 4.0 | 15% | 8 项回归通过；真实恢复 Screen Studio 录制并确认保存成功 | 尚缺多设备和长期批量结果 |
| 价值飞轮潜力 | 2.5 | 15% | 保护路径和故障案例可持续沉淀 | 默认不收集跨用户数据，案例积累依赖主动反馈 |
| 维护与交付效率 | 3.0 | 10% | Python 标准流程清晰，默认预览并有结构化状态 | macOS、应用目录和外置卷行为会持续变化 |
| 复制与渠道可控性 | 2.0 | 10% | 版本、Release 和官网目录可追踪 | 公开源码易复制，升级承接能力有限 |

加权评分约 3.5 / 5，对应标准到专业交付。139 Credits 是当前转化测试价，不代表成本或用户价值上限。

## 买家得到什么

用户得到一条目标容量驱动的 macOS 磁盘整理流程：建立真实容量基线，只读盘点，优先处理可重建候选，对重要低频资料执行可校验迁移，对回滚项做精确回收，最后回读容量与链接状态。v0.4.0 额外保护 Screen Studio 录制工作区、其后代和包含它的父目录，并让清理与迁移共享同一保护边界。

适用边界：只自动处理明确可重建产物和用户确认的低频资料。照片、消息、邮件、Git 历史、Agent 会话、应用托管工作区和用户显式保护路径不进入自动清理或迁移。外置卷断开时，归档链接可能暂时不可用。

## 渠道与推广

- 在 LovStudio 官网以 139 Credits 一次性解锁，突出“先盘点、可回滚、真实验收”和 Screen Studio 真实恢复案例。
- 用错误前后证据、保护边界拒绝输出和实际保存成功作为结果样例，而不是只展示释放容量数字。
- 源码保持公开，付费解锁不提供源码保密；团队存储审计、批量策略配置或迁移落地服务另行约定，不在当前 Skill 内承诺人工支持。

## 风险、假设与复评

- 使用风险：macOS 权限、运行中应用、动态文件、外置卷挂载和第三方应用目录可能随版本变化；任何执行都应保留预览和回滚证据。
- 假设：成本来自回溯工时区间与时薪假设；价值锚点来自 30 分钟至半天的保守省时和一次应用工作区故障恢复，没有把潜在数据损失按最高金额计入。
- 证据缺口：缺少连续 10 次不同机器运行、误报率、平均释放量和长期支持工时；目前仅有一个完整 Screen Studio 故障闭环及 8 项自动化回归。
- 复评触发：首发 30 天、100 次付费兑换、版本变化、出现新的应用工作区误判，或维护支持成本明显变化。

## 机器可读摘要

```json
{
  "skill_id": "clean-mac",
  "version": "0.4.0",
  "currency": "Credits",
  "billing_model": "one_time",
  "recommended_price": 139,
  "launch_price": 139,
  "price_range": [139, 139],
  "delivery_mode": "public_source",
  "latest_verified_free_space_gb": 196.54,
  "latest_verified_gain_gb": 173.35,
  "weighted_score": 3.5,
  "channel": "LovStudio Skill Publisher",
  "assumptions": ["18–28 build hours", "6–10 maintenance/support hours over 6 months", "direct infrastructure cost is near zero"],
  "evidence_gaps": ["10-run cross-device evidence", "false-positive rate", "long-term support hours"],
  "confidence": "case-backed",
  "review_trigger": "30 launch days, 100 paid redemptions, a version change, a new app-workspace false positive, or material support-cost change"
}
```
