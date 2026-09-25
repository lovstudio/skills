# Codex 会话阅读 · Codex Session Reader

![Version](https://img.shields.io/badge/version-0.1.1-CC785C)

读取 Codex task 状态、近期回合摘要和完成结果。

## 本地安装

在本仓库根目录执行：

```bash
export SKILL_SOURCE_DIR="$(pwd)"
mkdir -p "${SKILL_SKILLS_INSTALL_DIR:?请设置本地 Skills 目录}"
ln -s "$SKILL_SOURCE_DIR"   "$SKILL_SKILLS_INSTALL_DIR/lov-read-codex-session"
```

## 用户 Profile（跨 session）

每个生成的 Skill 都会在 `skill.yaml` 中声明 `user-profile/v1`，并从共享
Profile 读取用户、品牌、工作区和本 Skill 的长期记录。用户直接说出的持久
偏好或品牌事实由 `scripts/profile_store.py` 写回 Profile；源代码保持可移植。

详见 [`references/user-profile.md`](references/user-profile.md)。

## 使用

示例：输入当前 task，输出运行状态、最新进展与阻塞；输入 thread UUID，输出最近回合和最终结果。

宿主没有 Codex 线程工具时（例如 Claude Code），运行本地只读读取器：

```bash
python3 scripts/read_codex_session.py '<thread-uuid-or-deeplink>' --turns 3
python3 scripts/read_codex_session.py '<thread-uuid-or-deeplink>' --json
```

脚本读取 `$CODEX_HOME/sessions` 与 `$CODEX_HOME/archived_sessions`，只读且不输出完整转录。

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
