# Skill Pricing Card：lov-sync-with-synology

| 项目 | 结论 |
| --- | --- |
| 版本 / 交付单元 | 1.0.1 / 公开 Skill 源码、`synology-cli`、安装脚本和本地验证夹具 |
| 目标买家 | 需要把本地文件迁移到群晖 NAS 的个人开发者、创作者和小团队 |
| 建议价格 | 0 Credits |
| 稳定价格带 | 0 Credits，保持公开免费入口 |
| 首发测试价 | 0 Credits，持续到 10 次外部真实使用或加入托管服务 |
| 渠道 | LovStudio 官网 Skill Publisher |
| 置信度 | case-backed；真实大文件迁移数据仍然有限 |

## 为什么是免费

- 成本底线：约 8–14 小时研发、测试和文档，外加每半年约 4–8 小时维护；无托管服务、专有数据或固定 API 成本。
- 价值锚点：一次批量迁移预计节省 20–60 分钟的逐文件操作、校验和清理，并显著降低“接口成功但文件损坏、却已删除本地副本”的风险。
- 价格位置：六维加权结果约 2.7/5。能力真实且可验收，但替代方案较多、QuickConnect relay 维护风险较高，当前由维护者承担成本，作为免费公开入口。
- 证据边界：已有 7 个真实 MP3、约 60.6 MB 的本地 HTTPS 仿真验收，覆盖上传、MD5、回收站、重复运行和故障保护；尚缺跨设备、大文件和长期使用数据。

## 六维评分

| 维度 | 分数 / 5 | 权重 | 加分事实 | 扣分事实 |
| --- | ---: | ---: | --- | --- |
| 实际结果价值 | 3.5 | 30% | 结果是可观察的文件迁移；上传后有远端大小和 MD5 回读 | 使用场景集中在群晖 NAS，不是通用云盘迁移 |
| 稀缺性与替代难度 | 2.5 | 20% | QuickConnect 接入、MD5 校验和安全清理组成完整链路 | `rclone`、WebDAV、Synology Drive Client 可替代部分能力 |
| 质量证据与购买信心 | 3.5 | 15% | 有真实 MP3 端到端测试、故障注入、重复运行和解析器单元测试 | 尚无多台 NAS、DSM 版本和大文件长期统计 |
| 价值飞轮潜力 | 1.5 | 15% | 审计日志可以逐步积累迁移记录 | 单次事务为主，用户间没有明显网络效应 |
| 维护与交付效率 | 2.5 | 10% | CLI、配置、Keychain 和测试均可本地运行，无托管成本 | QuickConnect relay 依赖非公开协议，DSM 变化可能带来适配 |
| 复制与渠道可控性 | 1.5 | 10% | 版本、测试和线上更新可以形成信任差异 | MIT 公开源码复制门槛低 |

加权总分约 2.7 / 5；当前适合免费获客和口碑验证，不适合直接高价售卖。

## 买家得到什么

- 一条命令完成本地文件到群晖的传输：`QuickConnect / DSM HTTPS → File Station Upload`。
- 上传后校验远端大小和 MD5，只有全部通过才处理本地文件。
- 默认把本地文件移入可恢复的 trash；显式使用 `--delete-mode unlink` 才执行不可逆删除。
- 支持 macOS Keychain、配置档案、批量目录、审计 JSON 和已有远端文件幂等处理。
- 适用边界：需要可用的群晖账号、目标目录权限和网络；不包含 NAS 账号开通、C2 Object Storage、S3、远端删除或托管支持 SLA。

## 渠道与推广

- 在 LovStudio 官网免费提供，重点展示“先校验再删除”的安全结果，而不是堆叠 API 名称。
- 用真实测试结果说明：7/7 上传、7/7 MD5 一致、故障上传时本地文件不删除。
- 试用入口先展示 `doctor` 和 `--dry-run`，再展示正式迁移命令；收集 QuickConnect 环境和 DSM 版本反馈。
- 只有加入托管执行、企业权限适配、保证支持或大文件断点续传服务时，重新评估付费结构。

## 风险、假设与复评

- 使用风险：QuickConnect relay 属于社区协议；NAS 离线、别名变更、HTTPS 自签证书、权限和空间不足都会阻碍迁移。
- 假设：用户能自行提供 NAS 账号和目标目录，并接受本地 macOS Keychain 或环境变量保存凭据。
- 证据缺口：不同 DSM 版本、不同地区 QuickConnect 域名、大文件传输、多用户并发、长期成功率和维护工时。
- 复评触发：累计 10 次外部真实迁移、3 个以上非本人案例、版本变化、QuickConnect/DSM 协议变化，或加入托管、企业部署和保证支持。

## 机器可读摘要

```json
{
  "skill_id": "lov-sync-with-synology",
  "version": "1.0.1",
  "display_unit": "credits",
  "billing_model": "free_entry",
  "recommended_price_credits": 0,
  "launch_price_credits": 0,
  "price_range_credits": [0, 0],
  "weighted_score": 2.7,
  "channel": "LovStudio Skill Publisher",
  "assumptions": ["one batch saves 20-60 minutes and reduces local-copy deletion risk", "maintenance needs 4-8 hours per half-year"],
  "evidence_gaps": ["multi-version DSM coverage", "QuickConnect regions", "large-file transfer", "long-term success and maintenance cost"],
  "confidence": "case-backed",
  "review_trigger": "10 external real migrations, three non-author cases, version or protocol change, hosted service, enterprise deployment, or guaranteed support"
}
```
