# Claude 换号搬家 · Claude Account Mover

![Version](https://img.shields.io/badge/version-0.1.1-CC785C)

换了 Claude 桌面版账号后，把旧账号的 Code 会话和 Cowork 会话复制到当前账号，
在侧边栏里直接点开继续；顺带找出已经丢失对话记录的空壳会话，并把 Cowork 会话
的记录保留期调长，避免被 30 天自动清理。

## 为什么需要它

桌面版按账号分目录保存会话索引。换号后旧会话还在磁盘上，只是新账号看不到。
CC Switch 这类工具切换的是 API 供应商配置，不处理账号目录，所以帮不上忙。

## 安装

```bash
npx skills add lov-claude-account-migrate -g -y
```

本地源码安装：

```bash
ln -s "$(pwd)" "${SKILL_SKILLS_INSTALL_DIR:?请设置本地 Skills 目录}/lov-claude-account-migrate"
```

## 使用

对 Agent 说：

- “我换了 Claude 账号，把旧账号的 session 都搬过来”
- "I switched Claude accounts — migrate my old desktop sessions"

或直接运行脚本：

```bash
python3 scripts/claude_account_migrate.py scan                              # 看有哪些账号和会话
python3 scripts/claude_account_migrate.py migrate --from <旧账号>            # 预演
python3 scripts/claude_account_migrate.py migrate --from <旧账号> --apply    # 执行
python3 scripts/claude_account_migrate.py retention --account current --apply
```

`<旧账号>` 可以是 UUID、8 位以上前缀或可识别的邮箱；`--to` 默认是桌面版当前登录的账号。

示例输出（预演）：

```text
[plan] old-account-uuid -> current-account-uuid (org target-org-uuid)
  code  from org source-org-uuid: to copy 0, already present 0, orphans skipped 108 / copied 0, ...
  cowork from org source-org-uuid: to copy 77, already present 0, retention -> 3650d on 77, ...
    keep the source folder: 13 session(s) still write outputs there
```

## 安全边界

- 只复制，不覆盖目标已有文件，不修改、不删除旧账号目录。
- 不读取、不改动登录凭据、Keychain 和 App 配置。
- 默认只预演，加 `--apply` 才写入；重复执行是幂等的。
- 不迁移：claude.ai 网页聊天、Projects、connector 授权、云端会话、定时任务。
- 已被清理掉的对话记录无法恢复，这类会话默认跳过（`--include-orphans` 可保留标题）。

## 用户 Profile（跨 session）

在 `skill.yaml` 中声明 `user-profile/v1`。可记住的偏好：
`records.retention_days`、`records.include_orphans`。不保存邮箱、账号 ID 或凭据。
详见 [`references/user-profile.md`](references/user-profile.md)。

## 原子组合

见 [`references/skill-composition.md`](references/skill-composition.md)。搬迁项目目录交给
`lov-cc-mv`；本 Skill 是独立的 Single Skill。

## 可信度卡与用户案例

- [`skill-card.yaml`](skill-card.yaml) / [`skill-card.md`](skill-card.md)
- [`cases/cases.json`](cases/cases.json)
- [`pricing-card.yaml`](pricing-card.yaml)

## 质量门

```bash
python3 scripts/validate_skill.py .
```

## 依赖

- Python 3.9+（脚本只用标准库）
- PyYAML（仅校验器需要）

## License

MIT
