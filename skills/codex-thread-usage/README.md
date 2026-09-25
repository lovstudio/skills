# Codex 用量账本 · Codex Usage Ledger

![Version](https://img.shields.io/badge/version-0.1.1-CC785C)

从本地 Codex deeplink 或 thread UUID 生成可核验的 token usage 报告，并区分
整个线程累计值、最新 SQLite 快照、cached input 和 reasoning output。

## 本地安装

在本 Skill 源目录执行：

```bash
export SKILL_SOURCE_DIR="$(pwd)"
mkdir -p "${SKILL_SKILLS_INSTALL_DIR:?请设置本地 Skills 目录}"
ln -s "$SKILL_SOURCE_DIR" \
  "$SKILL_SKILLS_INSTALL_DIR/lov-codex-thread-usage"
```

## 用户 Profile（跨 session）

`skill.yaml` 声明 `user-profile/v1`。Skill 只读取语言、时区、工作区和自身
长期记录；不会把 thread ID、会话正文或本机路径写入 Profile。

## 使用

查看整个 thread 的明细：

```bash
python3 scripts/codex_thread_usage.py \
  'codex://threads/<thread-uuid>' --details
```

给脚本或统计系统使用 JSON：

```bash
python3 scripts/codex_thread_usage.py \
  '<thread-uuid>' --json
```

输出包含历史 processed tokens、input/cached/output/reasoning、TUI-style
non-cached total、SQLite 最新快照、累计计数段和质量警告。

## 原子组合

这是一个 Single Skill：deeplink 解析、SQLite 定位、rollout 扫描与统计属于同一
验收结果。相邻的账户额度查询、事实核验和经验沉淀均为可选交接，不是运行依赖。

## 可信度卡与用户案例

- `skill-card.yaml` / `skill-card.md`：用途、风险、输出和证据维度。
- `cases/cases.json`：脱敏后的真实 Input → Prompt → Output 案例。
- `pricing-card.yaml`：免费范围、价值和复评条件。

## 质量门

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/test_codex_thread_usage.py
python3 scripts/validate_skill.py .
```

## 依赖

- Python 3.9+
- Python 标准库
- 本地 Codex `state_5.sqlite` 与 rollout JSONL 的只读权限

## License

MIT
