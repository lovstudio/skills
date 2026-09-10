# Skill Group Composition

本记录说明 `lov-check-balance` 与相邻 Skill 的边界、交接和重叠处理。

## Nearby Skills Inspected

- `lov-env-management`：管理平台、账号与多组 API Key 的生命周期、有效期和启用
  状态，并同步到 shell 或会话环境。它拥有「凭据」，不回答「还剩多少额度」。
- `lov-yoda-automation`：创建、修复与核验定时任务，负责触发时间与通知。它拥有
  「何时跑、怎么通知」，不拥有额度语义。
- `lov-clean-mac`：磁盘空间清理与归档，与额度无关，明确不组合。
- `fix-codex-session-skill`：修复 Codex 会话与 provider 绑定，属于故障恢复，
  不是额度读取，不组合。
- `lov-solution-architect`：产出技术方案与选型，不承担运行时额度巡检。

## Atomic Handoffs

- 上游 `lov-env-management` → 本 Skill：交接物是「已存在且可用的凭据来源」
  （Keychain 服务名、环境变量名、cc-switch 数据库路径）。验收边界：凭据本身
  的有效性由上游负责，本 Skill 只报告探测结果。
- 本 Skill → 下游 `lov-yoda-automation`：交接物是 `--json` 输出，其中
  `providers[].status`、`windows[].used_percent`、`alerts[]` 可作为触发条件。
  验收边界：定时与通知的可靠性由下游负责，本 Skill 只保证输出结构与退出码。
- 本 Skill → 用户：交接物是额度体检表与需要动作的条目。验收边界：只报告事实，
  不执行充值、购买或密钥轮换。

## Overlap Decisions

- 与 `lov-env-management` 存在「同一批账号」的主题重叠，但能力不重叠：本 Skill
  不读写 Key 的元数据账本，只做一次只读探测。两者保持独立，通过凭据来源名对齐。
- 不新增「余额充值」「订阅比价」能力：那属于计费操作与商业决策，超出只读边界。
- 不把定时逻辑内嵌进来：单次探测是确定性的，调度属于下游 Skill 的职责。

## Composition Decision

选择 Single Skill，而不是 Skill Kit。理由是只有一个用户可见结果：额度体检表。
所有 provider 探测共享同一上下文、同一输出 schema 与同一只读不变量，拆成模块
只会增加调用成本。上下游通过明确工件协作，不构成硬依赖。
