# 额度体检 · Check Balance

> 这个 skill 可以看到你多个平台（例如 cc、codex、ds 等）的账号的用量，以及什么时候重置。

![Version](https://img.shields.io/badge/version-0.1.1-CC785C)

一条只读命令查清 Claude、Codex、DeepSeek 等 agent 账号还剩多少额度、什么时候
重置，以及按当前强度还能用多久。

## 本地安装

```bash
export SKILL_SOURCE_DIR="$HOME/.agents/skills/check-balance-skill"
mkdir -p "$HOME/.claude/skills"
ln -s "$SKILL_SOURCE_DIR" "$HOME/.claude/skills/lov-check-balance"
```

## 用户 Profile（跨 session）

`skill.yaml` 声明 `user-profile/v1`，从共享 Profile 读取用户、工作区、偏好与本
Skill 的长期记录。用户直接说出的持久偏好通过 `scripts/profile_store.py` 写回，
源代码保持可移植。详见 [`references/user-profile.md`](references/user-profile.md)。

## 使用

```bash
# 全量体检
python3 scripts/check_balance.py

# 只看深寻余额与本地网关消费
python3 scripts/check_balance.py --only deepseek --only gateway --gateway-log "$LITELLM_REQUEST_LOG"

# 估算消耗速率并输出 JSON，供定时任务消费
python3 scripts/check_balance.py --watch 120 --json
```

输出分为官方订阅（已用百分比与重置时间）和预付余额（剩余金额与消耗速率）两类；
每个 provider 独立标记 ok、expired 或 unavailable。

## 原子组合

`references/skill-composition.md` 记录了相邻 Skills 的检查结果：上游
`lov-env-management` 负责凭据生命周期，下游 `lov-yoda-automation` 负责定时与
通知，本 Skill 保持 Single Skill，不隐藏依赖任何 sibling。

## 可信度卡与用户案例

- `skill-card.yaml` / `skill-card.md`
- `cases/cases.json`
- `pricing-card.yaml`

## 质量门

```bash
python3 scripts/validate_skill.py .
```

## 依赖

- Python 3.8+（仅标准库）
- PyYAML（仅运行校验脚本时需要）

## License

MIT
