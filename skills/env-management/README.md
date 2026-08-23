# lov-env-management

![Version](https://img.shields.io/badge/version-0.1.0-CC785C)

面向软件开发的本地环境凭据账本：用“平台 → 账号 → Key”管理轮换、有效期与验证状态，安全投影到 zsh 或当前用户会话，并提供不显示秘密的 Dashboard。

## 能力边界

- 一个平台注册多个账号，一个账号保存多组轮换 Key。
- Registry 只存元数据；秘密可放 macOS Keychain、权限为 `0600` 的本地 vault、1Password 引用或已有环境变量。
- 同一个 target/变量名只有一个生效 binding，切换时不会复制 export。
- 支持生效时间、过期时间、远端 probe、人工验证状态和到期审计。
- `~/.zshenv` 只包含受管理的 source 块；实际导出文件权限为 `0600`。
- 本地 Dashboard 只展示脱敏数据，不录入或回显 Key。

## 本地安装

在 Skill 源目录执行：

```bash
export SKILL_SOURCE_DIR="$(pwd)"
mkdir -p "$HOME/.agents/skills" "$HOME/.claude/skills"
ln -s "$SKILL_SOURCE_DIR" "$HOME/.agents/skills/lov-env-management"
ln -s "../../.agents/skills/lov-env-management" "$HOME/.claude/skills/lov-env-management"
```

## 快速开始

```bash
python3 scripts/env_manager.py init
python3 scripts/env_manager.py add \
  --platform openai --account personal --key primary \
  --env-var OPENAI_API_KEY --backend auto
python3 scripts/env_manager.py bind \
  --target shell --env-var OPENAI_API_KEY openai/personal/primary
python3 scripts/env_manager.py sync-shell --rcfile "$HOME/.zshenv"
python3 scripts/env_manager.py sync-shell --rcfile "$HOME/.zshenv" --apply
python3 scripts/env_manager.py audit
```

新增命令会隐藏输入。自动化时使用 `--secret-stdin` 从标准输入读取；CLI 不接受会落入 shell history 的 `--value` 参数。

## 多账号和 Key 轮换

旧 Key 不需要覆盖。为新 Key 使用新 ID，完成真实验证后再切换 binding：

```bash
python3 scripts/env_manager.py add \
  --platform openai --account work --key rotation-2026-08 \
  --env-var OPENAI_API_KEY --status standby
python3 scripts/env_manager.py probe openai/work/rotation-2026-08 \
  --url https://api.openai.com/v1/models --auth bearer
python3 scripts/env_manager.py status openai/work/rotation-2026-08 --status active
python3 scripts/env_manager.py bind \
  --target shell --env-var OPENAI_API_KEY openai/work/rotation-2026-08
```

## Dashboard

```bash
python3 scripts/env_manager.py dashboard --open
```

页面只监听本机回环地址。可以筛选平台和账号、查看到期与验证状态、切换 target binding、更新非秘密状态；Key 值从不进入页面。

## 用户 Profile（跨 session）

`skill.yaml` 声明 `user-profile/v1`，用于默认后端、到期预警天数、Shell rc 和 Dashboard 打开偏好。Key 值与秘密引用不会写入 Profile。详见 [references/user-profile.md](references/user-profile.md)。

## 原子组合

[references/skill-composition.md](references/skill-composition.md) 记录了与 1Password、zsh alias、单平台 API 接入和 AI 集成 Skill 的边界。本 Skill 是单一 Skill；外部能力只接收脱敏变量清单或提供秘密引用。

## 质量门

```bash
python3 scripts/validate_skill.py .
python3 -m unittest discover -s tests -v
```

## 依赖

- Python 3.9+（标准库）
- 可选：macOS Keychain 的 `security`
- 可选：1Password CLI `op`
- Shell 投影需要 zsh；系统投影需要 `launchctl` 或 `systemctl --user`

## License

MIT
