---
name: lov-fix-codex-provider
description: >
  修复 Codex 打不开：把 thread 里持久化的 provider（yoda、custom 等）与 config.toml 实际定义对齐，先只读取证，再带备份重打标签。Use when Codex cannot open or resume a thread with Model provider not found.
license: MIT
compatibility: "Portable Agent Skills format. Python 3.8+ standard library; reads local Codex config, SQLite state and desktop logs; no network and no credentials."
metadata:
  author: skill-publisher
  version: "0.1.0"
  card_standard: lovstudio/skill-card/v1
  content_class: deterministic-output
  tags:
    - codex
    - provider
    - recovery
    - diagnostics
---

# Codex Provider 修复 · Codex Provider Repair

Codex 给每条 thread 持久化一个 provider id，但不同入口读到的 provider 集合不一样：
桌面 App 和普通 CLI 只读 `config.toml`，Yoda 这类集成会在启动时用 `-c` 参数注入
provider。两边不一致时，打开或 resume 这条 thread 就会报
`failed to load configuration: Model provider ... not found`，界面上表现为「打不开」。
本 Skill 先取证，再在带备份的前提下把两边对齐。

## Triggers

### Activate when

- 用户说“codex 打不开”“这条会话恢复不了”“thread can't resume”，或贴出 `Model provider ... not found`、`failed to load configuration`、`invalid_config`。
- 用户在桌面 App 里打开某条会话失败，但同一台机器上其他会话正常。
- Use when the Codex desktop app cannot open or resume a conversation and the machine has several persisted providers.
- 需要盘点本机有哪些 thread 的 provider 已经不存在，再决定补定义还是重打标签。

### Do not activate when

- 用户要读某条 thread 的进度或结果；交给 `lov-read-codex-session`。
- 用户要打开一条已知正常的 thread；交给 `lov-open-codex-session`。
- 报错是 `No tool output found for tool call`；交给 `lov-fix-deepseek-tool-call-error`。
- 要修的是 Codex 或 Yoda 的产品代码缺陷；走常规工程修复流程。

## Outputs

- 只读诊断报告：活跃 provider、已定义 provider、按 provider 分组的 thread 数量、
  桌面 App 日志里的 resume 失败次数、rollout 与索引不一致样本。
- 修复方案与可直接执行的命令；默认先打印计划，只有显式确认才写入。
- 修复后的回读结果与备份路径，可随时回滚。

## Workflow (MANDATORY)

### Step 0: Resolve skill root and dependencies

- 优先使用 `SKILL_DIR`；否则按当前 Skill 上下文推断安装目录。
- 确认 `scripts/codex_provider_doctor.py` 存在；缺失时先报出期望路径，不产出半成品。
- 默认只读。`--fix-retag` 与 `--restore` 是仅有的两个写入模式，且都必须带 `--yes`。

### Step 1: Collect evidence (read-only)

```bash
python3 "$SKILL_DIR/scripts/codex_provider_doctor.py"
```

- 数据源：`~/.codex/config.toml`、`~/.codex/state_5.sqlite` 的 `threads` 表、
  `~/.codex/logs_2.sqlite`，以及桌面 App 日志 `~/Library/Logs/com.openai.codex`。
- `--json` 输出结构化报告；`--logs-days N` 控制日志回看窗口；`--sample-rollouts N`
  控制 rollout 抽样条数。
- 大机器上全量扫描只需要几秒；报告不打印任何密钥值，只标记是否存在内联凭据。

### Step 2: Classify the failure

- **A. 启动即失败**：`config.toml` 里 `model_provider = "x"`，但没有
  `[model_providers.x]`。任何入口都起不来，先补定义。
- **B. 历史 provider 缺失**：thread 索引里存在配置中没有的 provider，桌面 App
  `thread/resume` 返回 `-32600 invalid_config`，这就是「会话打不开」。
- **C. rollout 与索引不一致**：`threads.model_provider` 和 rollout 首行
  `session_meta.payload.model_provider` 不同。两处都要修，否则修完仍会被旧值覆盖。

### Step 3: Choose the repair branch

- **仍在使用的共享 provider 桶（如 `yoda`、`custom`）→ 补定义**：这些 id 由集成方
  刻意保持稳定，重打标签会让对方的历史视图对不上。用
  `--print-provider-snippet <id> --like <existing>` 生成 `[model_providers.<id>]`
  片段，粘贴进 `~/.codex/config.toml`，然后完全退出并重启桌面 App。
  片段默认给 `env_key` 形式；GUI 启动的 App 读不到 shell 环境变量时，改用与现有
  provider 相同的内联凭据写法。
- **已退役 provider（如 `lovbrowser`、`nebula`、`xxx`）→ 重打标签**：把历史
  thread 指到当前可用 provider。

```bash
python3 "$SKILL_DIR/scripts/codex_provider_doctor.py" \
  --fix-retag custom --only-provider lovbrowser
```

- provider 是否仍在使用不确定时，先按共享桶处理（补定义），或先跑一次 dry-run
  看影响范围。

### Step 4: Apply the repair

- 先完全退出 Codex 桌面 App。脚本检测到 App 或 app-server 守护进程在运行时会拒绝
  写入；确认无风险时才用 `--force`。
- 重打标签命令加 `--yes` 才真正执行；不加时只打印计划：

```bash
python3 "$SKILL_DIR/scripts/codex_provider_doctor.py" \
  --fix-retag custom --only-provider xxx --yes
```

- 写入前自动备份到 `~/.codex/provider-repair-backups/<timestamp>/`：索引库的完整
  副本，加上每个被改写 rollout 的首行原文。回滚：

```bash
python3 "$SKILL_DIR/scripts/codex_provider_doctor.py" \
  --restore ~/.codex/provider-repair-backups/<timestamp> --yes
```

- rollout 文件很大时可先只改索引（`--skip-rollouts`），但要在结果里说明 rollout
  session_meta 尚未同步；默认两者都改。
- 本 Skill 不自动修改 `config.toml`。补定义是人工粘贴步骤，避免覆盖用户的切换器配置。

### Step 5: Verify and report

- 复跑 `scripts/codex_provider_doctor.py`，确认目标 provider 从缺失列表消失，
  `--sample-rollouts` 抽样不再出现索引与 rollout 不一致。
- 让用户在重新启动的桌面 App 里打开目标会话；CLI 用
  `codex resume <thread-id>` 验证能进入会话。
- 报告必须区分：已取证 / 已修复 / 已回读 / 仍待用户确认，并给出版本边界
  （本机验证基于 codex-cli 0.153.4 与 Codex Desktop 26.903.71938）。

## References

- `references/mechanism.md`：provider 解析链路、失败形态与真实证据。
- `references/repair.md`：补定义与重打标签的详细步骤、备份与回滚、验证清单。
- `references/skill-composition.md`：与相邻 Skills 的边界与交接。

## Dependencies

- Python 3.8+ 标准库；可选 PyYAML 仅用于 `scripts/validate_skill.py`。
- 读取本地 Codex 目录与桌面 App 日志的权限；无网络、无凭据。
- 相邻能力（可选，不构成硬依赖）：`lov-read-codex-session` 读 thread 状态，
  `lov-open-codex-session` 打开会话，`lov-fix-deepseek-tool-call-error` 处理工具
  调用类故障。
