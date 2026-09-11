# Codex × DeepSeek 会话急救 · Codex × DeepSeek Thread First Aid

![Version](https://img.shields.io/badge/version-0.1.0-CC785C)

把 Codex 在 DeepSeek 会话里的 `No tool output found for tool call` 400 变成一份可盘点、
可恢复、可预防的清单。

## 本地安装

```bash
export SKILL_SOURCE_DIR="$(pwd)"
mkdir -p "${SKILL_SKILLS_INSTALL_DIR:?请设置本地 Skills 目录}"
ln -s "$SKILL_SOURCE_DIR" "$SKILL_SKILLS_INSTALL_DIR/lov-fix-deepseek-tool-call-error"
# 三层链约定：中间层指向真源，宿主层用相对路径指向中间层
ln -s "../../.agents/skills/lov-fix-deepseek-tool-call-error" \
  "$HOME/.claude/skills/lov-fix-deepseek-tool-call-error"
```

## 用户 Profile（跨 session）

本 Skill 在 `skill.yaml` 中声明 `user-profile/v1`，从共享 Profile 读取用户、品牌与工作区，
并把自己的长期记录写在 `skills.lov-fix-deepseek-tool-call-error.records`。用户直接说出的
持久偏好由 `scripts/profile_store.py` 写回。详见 `references/user-profile.md`。

## 使用

```bash
python3 scripts/scan_deepseek_sessions.py                 # 全量扫描默认会话目录
python3 scripts/scan_deepseek_sessions.py --file rollout.jsonl --json
python3 scripts/scan_deepseek_sessions.py --root ~/.codex/archived_sessions
```

输出示例（2026-09-11 本机实测）：

```text
time | session | victim | batch | variant | repeats
05:40:36 | 01a08ee7 | view_image | exec_command,view_image | image_batch_with_resize_notice | x3
08:36:48 | 01a08f9c | exec_command | exec_command,view_image | image_batch_with_resize_notice | x1

incidents=8 sessions=6 wedged=1
```

## 原子组合

`references/skill-composition.md` 记录已检查的相邻 Skills、可选交接与 Single Skill 决策：
读 thread 状态交给 `lov-read-codex-session`，外部看图交给 `lov-describe-image`，复发记账
交给 `lov-feedback-loop`，三者都不是硬依赖。

## 可信度卡与用户案例

- `skill-card.yaml` / `skill-card.md`：用途、负责人、依赖、风险、输出与维度地图。
- `cases/cases.json`：2026-09-11 六条 thread 被同一 400 锁死的真实案例。
- `pricing-card.yaml`：免费价值锚点、交付边界与复评条件。

## 质量门

```bash
python3 scripts/validate_skill.py .
```

## 依赖

- Python 3.8+ 标准库；PyYAML 仅用于校验脚本。
- 本地 Codex 会话目录读权限；无网络。

## License

MIT
