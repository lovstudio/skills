# Skill Group Composition

This record prevents adjacent Skills from becoming accidental duplicates or
hidden dependencies. This Skill is intentionally a Single Skill.

## Nearby Skills Inspected

- `lov-better-project-structure` — 单个代码仓库或 monorepo 的目录职责、import、构建路径与测试发现。输入/输出是代码项目结构；与本 Skill 的整盘项目分类不同，不合并。
- `lov-migrate-camera-media` — 相机卡/存储卡的首次转存、SHA-256 回读、整卡目录保留与授权清卡。它产出 `原始素材/`、`处理素材/`、`转存校验/` 约定；本 Skill 只接收已完成的转存目录，并保留这些内部约定。
- `lov-clean-mac` — Mac 本地磁盘清理、迁移、容量验证。它负责删除或归档本机文件；本 Skill 不删除，只做同卷 rename 和迁移记录。
- `lov-safe-dedupe` — 重复文件的全量哈希、隔离与删除门禁。当前会话尚未安装；本 Skill 只输出只读的 copy-suffix 信号，不执行删除。
- `lov-rename-project` — 重命名单个项目、路径或仓库并保持兼容键和运行连续性。它是项目级重命名，不负责盘级分类。
- `lov-branding-consistency` — 面向公开读者的文案审校。只有把迁移报告发布给外部读者时才交接；迁移路径、JSON、日志和校验记录不做品牌改写。

## Atomic Handoffs

- Upstream: `lov-migrate-camera-media` 输出已验证的相机卡目录。本 Skill 接收该目录，保持其内部 `原始素材/`、`处理素材/`、`转存校验/` 结构，不改写校验记录。
- Core: inventory → project-first taxonomy → minimal move map → plan validation → user confirmation → same-volume apply → verify.
- Downstream: copy-suffix 或同名同大小候选交给 `lov-safe-dedupe`，由后者执行全量 SHA-256、隔离和删除门禁。
- Downstream: Mac 本地缓存或本地容量释放交给 `lov-clean-mac`。
- Downstream: 目标其实是单个代码仓库时交给 `lov-better-project-structure`。
- No handoff: 系统目录、回收站、唯一副本和运行中的 app 库不交给任何自动删除能力。

## Overlap Decisions

- 与 `lov-better-project-structure` 的重叠只在“目录整理”这四个字，输入、风险和验收完全不同，保持两个 Skill 分离。
- 与 `lov-rename-project` 的重叠只在“路径变化”，本 Skill 负责盘级映射和批量回滚，不处理单个项目的兼容键。
- 与 `lov-safe-dedupe` 的重叠只在“发现重复信号”，本 Skill 永不删除，后者才拥有删除权。
- 外部 sibling Skills 只通过用户可见的制品交接，不作为本 Skill 的隐藏运行依赖。

## Composition Decision

Single Skill。inventory、taxonomy、plan、apply、verify 共享同一套安全门禁、同一份 mapping 和同一份 rollback；把它们拆成 Kit 只会把高风险步骤分散到多个上下文。确定性逻辑放在 `scripts/storage_organizer.py`，领域规则放在 `references/`。
