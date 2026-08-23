# lov-ataru-indexing

![Version](https://img.shields.io/badge/version-0.2.0-CC785C)

把本机 Ataru 会话记忆索引带到可检索状态，并交回一份能直接判断的 JSON 报告。

## 本地安装

在本仓库根目录执行：

```bash
export SKILL_SOURCE_DIR="$(pwd)"
mkdir -p "${SKILL_SKILLS_INSTALL_DIR:?请设置本地 Skills 目录}"
ln -s "$SKILL_SOURCE_DIR" "$SKILL_SKILLS_INSTALL_DIR/lov-ataru-indexing"
```

## 用户 Profile（跨 session）

`skill.yaml` 声明 `user-profile/v1`，从共享 Profile 读取用户、品牌、工作区，以及
本 Skill 的长期记录。这里唯一值得保存的是 `records.ataru_bin` —— 本机可用的
Ataru 可执行文件路径，由 `scripts/profile_store.py` 写回，源码保持可移植。

详见 [`references/user-profile.md`](references/user-profile.md)。

## 使用

```bash
# 只看状态，不动索引
python3 scripts/ataru_index.py status

# 幂等地把索引带到可检索状态
python3 scripts/ataru_index.py ensure --timeout 3600

# 用户明确要求完全重建时
python3 scripts/ataru_index.py ensure --force
```

`status` 在原始状态之上给出 `needsBuild` / `isBuilding` / `progressPercent`；
`ensure` 在 `actions` 里说明这次实际做了什么（`already-ready`、`catch-up-build`、
`waited-for-running-build`、`full-rebuild`）。索引不可用时退出码为 1。

二进制解析顺序是 `--bin` → `ATARU_BIN` → PATH → 已安装 App bundle → 本地 dev
build，并对每个候选先跑一次 `--version`：低于 0.41.3 的旧版不认识 `index status`，
会把它当成桌面启动参数打开窗口，因此版本门必须前置。

## 原子组合

见 [`references/skill-composition.md`](references/skill-composition.md)。本源码是
独立 Single Skill；与 `lov-ataru-search` 只有制品级交接。

## 可信度卡与用户案例

- [`skill-card.yaml`](skill-card.yaml) / [`skill-card.md`](skill-card.md)
- [`cases/cases.json`](cases/cases.json)
- [`pricing-card.yaml`](pricing-card.yaml)

## 质量门

```bash
python3 scripts/validate_skill.py .
```

## 依赖

- Python 3.8+（仅标准库）
- 本机安装的 Ataru 0.41.3 或更新版本

## License

MIT
