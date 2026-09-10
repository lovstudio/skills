# 存储整理师 · Storage Organizer

![Version](https://img.shields.io/badge/version-0.1.0-CC785C)

按项目、用途与生命周期盘点整块存储盘，规划同卷安全重命名与迁移，输出映射、回滚记录和不可删除门禁。

## 本地安装

在本仓库根目录执行：

```bash
export SKILL_SOURCE_DIR="$(pwd)"
mkdir -p "${SKILL_SKILLS_INSTALL_DIR:?请设置本地 Skills 目录}"
ln -s "$SKILL_SOURCE_DIR" \
  "$SKILL_SKILLS_INSTALL_DIR/lov-organize-storage"
```

## 用户 Profile（跨 session）

每个生成的 Skill 都会在 `skill.yaml` 中声明 `user-profile/v1`，并从共享
Profile 读取用户、品牌、工作区和本 Skill 的长期记录。用户直接说出的持久
偏好或工作区事实由 `scripts/profile_store.py` 写回 Profile；源代码保持可移植。

详见 [`references/user-profile.md`](references/user-profile.md)。

## 使用

只读盘点：

```bash
python3 scripts/storage_organizer.py inventory \
  --root "/Volumes/Example" \
  --sizes \
  --out /tmp/storage-inventory.json
```

生成并校验迁移计划：

```bash
python3 scripts/storage_organizer.py plan \
  --root "/Volumes/Example" \
  --map /tmp/storage-move-map.json \
  --out /tmp/storage-move-plan.json
```

确认后执行同卷 rename：

```bash
python3 scripts/storage_organizer.py apply \
  --plan /tmp/storage-move-plan.json \
  --confirm \
  --log-dir "/Volumes/Example/99_管理/迁移记录_2026-09-10"
```

逐项验收：

```bash
python3 scripts/storage_organizer.py verify \
  --plan /tmp/storage-move-plan.json \
  --log-dir "/Volumes/Example/99_管理/迁移记录_2026-09-10"
```

## 原子组合

`references/skill-composition.md` 记录已检查的相邻 Skills、可选交接、重叠处理，
以及为何本 Skill 选择 Single Skill。代码仓库结构、相机卡转存、重复删除和
Mac 本地清理均由相邻能力负责，本 Skill 不把它们变成隐藏依赖。

## 安全默认值

- 默认只读；`apply` 需要显式 `--confirm`。
- 只做同卷 rename，不跨卷复制。
- 不删除、不覆盖、不格式化。
- `.Trashes`、`.Spotlight-V100`、`.fseventsd` 等系统目录保持原样。
- 回收站只有在唯一副本得到独立备份确认后才允许清空。
- 每次执行都留下 `mapping.json` 与 `rollback.sh`。

## 可信度卡与用户案例

- [`skill-card.yaml`](skill-card.yaml) / [`skill-card.md`](skill-card.md)
- [`cases/cases.json`](cases/cases.json)
- [`pricing-card.yaml`](pricing-card.yaml)

## 质量门

```bash
python3 scripts/validate_skill.py .
```

## 依赖

- Python 3.8+
- PyYAML
- macOS 或 Linux 下的常用 shell 工具

## License

MIT
