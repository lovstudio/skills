# 组合决策

本 Skill 由 `lov-publish-wechat-channels` 升级而来，2026-08-18 扩成双平台。这里记录它和
相邻 Skill 的边界，以及为什么选了当前形态。

## Nearby Skills Inspected

| Skill | 职责 | 与本 Skill 的关系 |
| --- | --- | --- |
| `lov-publish-wechat-channels` | 只发微信视频号 | 本 Skill 的前身，已标记 deprecated 并指向这里 |
| `lov-publish-wechat-article` | 发微信公众号图文 | 不重叠：图文接口与视频后台是两套东西 |
| `lov-media-creator` | 剪辑、渲染、封面与系列规范 | 上游：它产出成片和封面，本 Skill 只负责把文件送上平台 |

系列名的两个形态（全称 / 短名）由 `lov-media-creator` 的 series-template 定义，本 Skill 只
执行「默认全称、降级必须有实证」这条判据，不自行改名。

## Atomic Handoffs

- **入口**：一个本地视频文件、一份文案、零到多张封面图，加上目标平台与目标动作。
- **出口**：状态契约里的一个终态，附列表回读证据（条目链接或 ID / BV 号）。
- 不生成、不重压、不重剪素材。唯一例外是平台明确拒绝转码时，按重压方案消除预检偏离项——
  那是为了让同一份内容通得过，不是二次创作。
- 不写文案主体。用户没给全时只做克制补齐，证据不足就停在提交前报缺项。

## Overlap Decisions

- **视频预检**与 `lov-media-creator` 的导出检查有重叠，但判据不同：这里查的是**平台**硬
  限制（大小、时长）和转码风险，creator 那边查的是画面与响度。两边都保留，各自按自己的
  阈值报。
- **封面合成**属于 creator；本 Skill 只验安全区与槽位对应关系。B 站 16:9 槽需要一张竖版
  素材横过来时，合成配方记在 B 站约束文档里，执行仍走 creator。
- **浏览器自动化**的 helper 签名坑、控制权规则、任务空间生命周期全部集中在
  `references/browser-workflow.md`，不在两份 page-anatomy 里重复。

## Composition Decision

**选单 Skill，不拆 Kit。** 两个平台的 DOM 与写值方式几乎没有交集，一度考虑做成
controller + 两个平台 module 的 Kit；最后按用户决定收敛为一份 SKILL.md 加按平台分目录的
references。

判据：

- 流程骨架两边是同一套——预检 → 上传 → 填字段回读 → 终稿确认 → 提交 → 列表回读。差异
  集中在「怎么写值」和「硬限制是多少」，这两类都能靠 references 分目录和脚本的
  `--platform` 参数隔开，不需要拆运行时。
- 拆 Kit 会把「终稿确认」「列表回读」这类必须一致的门禁复制两份，日后一定漂移。
- 加第三个平台时的增量是：一对 references + 脚本平台表里加一项 + SKILL.md 路由表加一行，
  代价可接受。

**旧 Skill 保留但 deprecated。** 已有会话与快捷方式还在用 `lov-publish-wechat-channels`
这个名字，直接删会让触发失败且没有提示。它的 SKILL.md 顶部加了弃用说明并指向本 Skill。

**B 站知识只有一份来源。** 原先散在项目 AGENTS.md 里的 20 条实测判据已移植进
`references/bilibili/` 并从 AGENTS.md 删除，避免两份互相漂移。
