# 存储整理师 · Storage Organizer · Skill Card

## Description

按项目、用途与生命周期盘点整块存储盘，规划同卷安全重命名与迁移，输出映射、回滚记录和不可删除门禁。

## Owner

contributors · local-skill-source

## License / Terms

MIT。允许在本地 Agent 宿主中使用、修改与分发；保留来源与许可证。

## Use Case

面向需要整理外置盘、归档盘或大型目录的个人与团队。典型输入是混合了相机项目、个人归档、成片、app 数据、安装包与系统目录的根目录；典型输出是项目制一级分类、同卷迁移计划、mapping、rollback 和验收报告。

## Deployment Geography

本地运行。适用于 macOS 与 Linux；不依赖外部服务或云账户。

## Requirements / Dependencies

- Python 3.8+
- PyYAML（仅校验脚本需要）
- 可读写的目标存储卷
- 同卷 rename 权限
- 不需要凭据、网络或第三方 API

## Known Risks and Mitigations

- 移动正在使用的项目或 app 库会破坏绝对路径：先做 48 小时活跃检查、打开句柄检查、app 库门禁，并要求用户确认。
- 回收站里的唯一副本被误清空：回收站封存，本 Skill 永不删除。
- exFAT 的 AppleDouble sidecar 与目标文件分离：apply 自动携带并在 verify 中检查配对。
- 历史 JSON/日志中的绝对路径失效：不改写历史证据，生成 old → new 的 mapping。

## References

- [Primary Skill instructions](SKILL.md)
- [Project-first taxonomy](references/storage-taxonomy.md)
- [Safety gates](references/safety-gates.md)
- [Skill group composition](references/skill-composition.md)

## Skill Output

输出类型包括 inventory JSON、move plan JSON、mapping JSON、rollback shell script 和 verification report。验收检查覆盖同卷 rename、目标冲突、源消失与目标存在、sidecar 配对和迁移前后体积对账。

## Skill Version

0.1.0

## Ethical Considerations

不删除、不覆盖、不移动系统目录或唯一副本；保留历史日志与用户授权边界；不虚构验证结果或迁移完成状态。

## User Cases

See [cases/cases.json](cases/cases.json). Every case shows Input → Prompt → Output.

## Dimension Map

Machine-readable dimensions are in [skill-card.yaml](skill-card.yaml): safety, reversibility, traceability, portability. Scores remain null until real cross-user evidence exists.

## Pricing Basis

See [pricing-card.yaml](pricing-card.yaml). Free entry; value anchor is avoiding irreversible path breakage and sole-copy loss during a whole-volume reorganization.

## Distribution

Free channels: github, lovstudio. Paid channels: none selected. No channel is described as live before publication.
