# Codex Provider 修复 · Codex Provider Repair

![Version](https://img.shields.io/badge/version-0.1.0-CC785C)

把 Codex thread 里持久化的 provider 与 `config.toml` 实际定义的 provider 对齐，
解决「会话打不开 / 无法 resume / Model provider not found」。

## 问题是什么

Codex 给每条 thread 记录一个 provider id。桌面 App 和普通 CLI 只读
`~/.codex/config.toml`；Yoda 这类集成会在启动 Codex 时用 `-c` 参数注入自己的
provider（如 `yoda`）。集成建出来的 thread 在桌面 App 里打开时找不到该 provider，
app-server 返回 `-32600 invalid_config`，界面表现为这条会话打不开：

```text
failed to load configuration: Model provider `yoda` not found
```

同一台机器上，`custom` 被切换器临时改写后也会出现同一类报错。

## 本地安装

在本仓库根目录执行：

```bash
export SKILL_SOURCE_DIR="$(pwd)"
mkdir -p "${SKILL_SKILLS_INSTALL_DIR:?请设置本地 Skills 目录}"
ln -s "$SKILL_SOURCE_DIR" "$SKILL_SKILLS_INSTALL_DIR/lov-fix-codex-provider"
```

三层链路（共享入口在前，宿主入口指向共享入口）：

```bash
ln -s "$SKILL_SOURCE_DIR" "$HOME/.agents/skills/lov-fix-codex-provider"
ln -s "../../.agents/skills/lov-fix-codex-provider" \
  "$HOME/.claude/skills/lov-fix-codex-provider"
ln -s "../../.agents/skills/lov-fix-codex-provider" \
  "$HOME/.codex/skills/lov-fix-codex-provider"
readlink -f "$HOME/.codex/skills/lov-fix-codex-provider"
```

## 使用

只读取证：

```bash
python3 scripts/codex_provider_doctor.py
python3 scripts/codex_provider_doctor.py --json > provider-report.json
```

补定义一个仍在使用的 provider（人工粘贴进 `~/.codex/config.toml`）：

```bash
python3 scripts/codex_provider_doctor.py \
  --print-provider-snippet yoda --like custom --env-key DEEPSEEK_API_KEY
```

把已退役 provider 的历史 thread 重打标签（先 dry-run，再加 `--yes` 写入）：

```bash
python3 scripts/codex_provider_doctor.py --fix-retag custom --only-provider xxx
python3 scripts/codex_provider_doctor.py \
  --fix-retag custom --only-provider xxx --yes
```

回滚一次修复：

```bash
python3 scripts/codex_provider_doctor.py \
  --restore ~/.codex/provider-repair-backups/<timestamp> --yes
```

写操作前请完全退出 Codex 桌面 App；脚本检测到 App 或 app-server 在运行时会拒绝写入。

## Profile contract

本 Skill 声明 `user-profile/v1`（见 `skill.yaml`），每次运行读取 `user`、`brand`、
`workspace`、`preferences` 与 `skills.lov-fix-codex-provider` 作用域；用户直接说明
的长期偏好用 `scripts/profile_store.py record --confirm` 写回，并在结果里报告保存路径。

## 质量门

```bash
python3 scripts/validate_skill.py .
python3 scripts/test_codex_provider_doctor.py
```

## 依赖

- Python 3.8+ 标准库（`sqlite3`、`json`、`argparse`；无 tomllib 时使用内置简易解析）。
- PyYAML 仅用于 Skill 源校验。
- 无网络、无凭据；不打印任何密钥值。

## License

MIT
