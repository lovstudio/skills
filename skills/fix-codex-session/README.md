# 会话救援 · Session Rescuer

![Version](https://img.shields.io/badge/version-0.2.0-CC785C)

把一条无法继续的 Codex 线程诊断清楚：既处理 “tool call 没有配对的 tool
output”，也在切换 provider / 中转站后把过期 thread 的 provider 绑定同步到当前
`config.toml`，并从磁盘交付物接手或生成安全恢复路径。

## 本地安装

在本仓库根目录执行：

```bash
export SKILL_SOURCE_DIR="$(pwd)"
mkdir -p "${SKILL_SKILLS_INSTALL_DIR:?请设置本地 Skills 目录}"
ln -s "$SKILL_SOURCE_DIR"   "$SKILL_SKILLS_INSTALL_DIR/lov-fix-codex-session"
```

## 用户 Profile（跨 session）

每个生成的 Skill 都会在 `skill.yaml` 中声明 `user-profile/v1`，并从共享
Profile 读取用户、品牌、工作区和本 Skill 的长期记录。用户直接说出的持久
偏好或品牌事实由 `scripts/profile_store.py` 写回 Profile；源代码保持可移植。

详见 [`references/user-profile.md`](references/user-profile.md)。

## 使用

```bash
# 只读诊断：报告该线程所有 rollout 的健康与悬挂工具调用
python3 scripts/fix_codex_session.py "01a08678-4e04-74c0-a99c-b0fca72c526a" --json

# 生成一份修复副本（不覆盖原文件）
python3 scripts/fix_codex_session.py "01a08678-4e04-74c0-a99c-b0fca72c526a" --fix

# Provider 切换后，先只读检查过期绑定
python3 scripts/sync_thread_provider.py --json

# 退出 Codex Desktop 后，备份并统一旧 thread 的 provider
python3 scripts/sync_thread_provider.py --apply
```

示例：线程 `01a08678-…` 在生成 PDF 时崩溃，之后每次都复现
`No tool output found for tool call call_01_syEaRJl1e4cxiKx7Wp7t9659`。诊断定位到
一个悬挂的 `view_image` 调用；恢复路径是直接重新生成已被 Markdown 引用、但尚未
写入 PDF 的航班链图，产出 18 页的最终 PDF。完整背景见
[`references/troubleshooting.md`](references/troubleshooting.md)。

Provider 场景：CC Switch 从 DeepSeek 官方 API 切到 LiteLLM 后，旧 thread
仍记录 `model_provider = "custom"`，打开时报 `Model provider 'custom' not
found`。`sync_thread_provider.py` 只同步 `state_*.sqlite` 的
`threads.model_provider`，默认只迁移当前配置里已不存在的 provider，并保留
build-in `openai` 历史；它不会重写 rollout JSONL。

## 原子组合

每个新 Skill 都带有 `references/skill-composition.md`。它记录已检查的相邻
Skills、可选的上游/下游交接、重叠处理，以及为何选择 Single Skill 或自包含
Skill Kit；外部 sibling Skill 不作为隐藏依赖。

## 可信度卡与用户案例

每个新 Skill 都必须随源代码提供：

- `skill-card.yaml` / `skill-card.md`：用途、负责人、依赖、风险、输出与维度地图。
- `cases/cases.json`：至少一个真实的 Input → Prompt → Output 案例。
- `pricing-card.yaml`：免费或付费都要写清价值锚点、交付边界和复评条件。

## 质量门

```bash
python3 scripts/validate_skill.py .
```

## 依赖

- Python 3.8+
- PyYAML

## License

MIT
