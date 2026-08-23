---
name: lov-env-management
description: >
  统一管理平台、账号与多组 API Key，维护有效期和启用状态，安全同步到 zsh 或用户会话环境，并提供脱敏 Dashboard；用户说“管理环境变量”“rotate API keys”时使用。
license: MIT
metadata:
  author: contributors
  version: "0.2.0"
  card_standard: lovstudio/skill-card/v1
  tags:
    - environment
    - api-key
    - secrets
    - shell
    - dashboard
  compatibility: "Python 3.9+ standard library; macOS or Linux. Optional macOS Keychain and 1Password CLI backends."
  dependencies: []
---

# lov-env-management

把散落的开发环境变量收进“平台 → 账号 → Key”账本，明确每个 Key 的生命周期、验证状态和当前投影目标，并在不回显秘密的前提下同步 Shell 或用户图形会话环境。

## Triggers

### Activate when

- 用户说“管理我的环境变量”“同一个平台有多个账号和 API Key”“把这个 Key 轮换到 zsh”或“打开环境变量 Dashboard”。
- User asks to “manage API keys”, “rotate an environment variable”, “switch the active account”, or “audit expiring keys”.
- 用户需要维护 Key 的生效时间、过期时间、远端验证结果，或在多个 Key 中选择一个投影到指定变量。

### Do not activate when

- 用户只要给当前单次命令临时传一个环境变量；直接使用当前 Shell 的 invocation-scoped environment。
- 用户要把云端 Secret 写入 Vercel、GitHub Actions、Supabase 或 Kubernetes；使用目标平台的 Secret 管理流程，本 Skill 只可提供经过确认的变量名清单。
- 用户要管理登录密码、信用卡或恢复码；使用密码管理器。1Password 仅作为本 Skill 的可选秘密来源。
- 用户要新增 zsh 快捷命令或函数而不是环境变量；交给 `lov-zsh-alias`。

## Security Invariants

- 绝不把 Key 值写入聊天、Profile、日志、Dashboard、URL、命令参数或版本库。
- 新增 Key 只接受隐藏交互输入或标准输入；CLI 故意不提供 `--value`。
- Registry 只保存脱敏元数据。默认 macOS 使用 Keychain，其他系统使用权限为 `0600` 的本地 vault；也支持 `op://` 引用和已有环境变量引用。
- `~/.zshenv` 只写一个受哨兵标记管理的 `source` 块，实际导出位于权限为 `0600` 的生成文件。
- 同一 target 和变量名只允许一个 binding。切换账号或 Key 是替换 binding，不是复制多份 export。
- Dashboard 只绑定 `127.0.0.1`，不展示秘密，也不提供秘密录入框；所有写操作需要当前进程生成的临时 token 和同源请求。
- 不自动把 Key 写入 `/etc/environment`、LaunchAgent plist 或仓库 `.env` 文件。系统投影仅作用于当前用户会话，并要求显式确认进程环境暴露风险。

## User Profile (cross-session)

每次运行先读取 `skill.yaml` 声明的 `user-profile/v1`。Profile 只保存安全的工作偏好，例如默认秘密后端、过期预警天数、Shell rc 文件和 Dashboard 是否自动打开；所有 Key 值及秘密引用都留在专用存储，不进入 Profile。

当用户直接声明需要跨 session 保存的非秘密偏好时，通过 `scripts/profile_store.py record --skill-id lov-env-management --confirm` 写入 `records` 并报告保存路径。凭据、token、cookie 和任何 secret-like 字段不得写入 Profile。完整契约见 [references/user-profile.md](references/user-profile.md)。

## Skill Group Composition

运行前阅读 [references/skill-composition.md](references/skill-composition.md)。外部 Skill 只通过脱敏变量清单或秘密引用进行可选交接，不是隐藏依赖。

## Workflow (MANDATORY)

### Step 0: Resolve context and inspect without secrets

1. Resolve `SKILL_DIR`, then run `profile_store.py read` for safe defaults.
2. Resolve storage with this precedence: current CLI flag, `LOV_ENV_HOME`, Skill Profile, then the platform-safe config directory.
3. Start with `list` or `audit`; never search broad home-directory globs for credentials.
4. Separate requested targets: current command, zsh startup, current user GUI session, or a platform-specific remote Secret store.

```bash
python3 "$SKILL_DIR/scripts/env_manager.py" list
python3 "$SKILL_DIR/scripts/env_manager.py" audit
```

### Step 1: Model platform, account, and Key identity

Use stable kebab-case IDs. A Key locator is `platform/account/key`, for example `openai/personal/primary` or `openai/work/rotation-2026-08`.

Add every rotated Key as a new record so history stays attributable. Do not overwrite an existing key ID. Choose a secret backend automatically unless the user named one:

1. `keychain` on macOS when available;
2. `file` vault with mode `0600` elsewhere;
3. `op` for an explicit `op://` reference;
4. `env` only when an existing variable is the intended source.

```bash
python3 "$SKILL_DIR/scripts/env_manager.py" add \
  --platform openai --account personal --key rotation-2026-08 \
  --env-var OPENAI_API_KEY --backend auto \
  --status standby --expires-at 2026-12-31
```

The command prompts without echo. For automation, pipe the value and add `--secret-stdin`; never place it in a shell argument.

### Step 2: Maintain lifecycle and validity evidence

Read [references/data-model.md](references/data-model.md) before changing lifecycle fields.

- `active`: eligible for a binding.
- `standby`: stored for rotation but not preferred.
- `disabled`: temporarily excluded.
- `revoked`: permanently excluded; keep metadata for audit history.
- Effective health additionally accounts for `not_before`, `expires_at`, and the latest validation result.

Use `status` for administrative state and `probe` for remote evidence. `probe` sends the Key only in an HTTPS header, blocks redirects, never stores a response body, and records only origin, status code, time, and redacted result.

```bash
python3 "$SKILL_DIR/scripts/env_manager.py" status \
  openai/personal/rotation-2026-08 --status active

python3 "$SKILL_DIR/scripts/env_manager.py" probe \
  openai/personal/rotation-2026-08 \
  --url https://api.openai.com/v1/models --auth bearer
```

If a service cannot be probed generically, use `mark-validation --result valid|invalid|unknown` after a real platform-specific check and record a non-secret note.

### Step 3: Bind exactly one Key per target variable

Bindings are independent for `shell` and `system`. The binding is the atomic switch point for multiple accounts and multiple keys.

```bash
python3 "$SKILL_DIR/scripts/env_manager.py" bind \
  --target shell --env-var OPENAI_API_KEY \
  openai/personal/rotation-2026-08
```

Reject expired, invalid, disabled, revoked, or not-yet-valid Keys. Only use `--allow-unhealthy` when the user explicitly accepts the reason and the resulting risk.

### Step 4: Preview, apply, and verify environment projection

Read [references/environment-targets.md](references/environment-targets.md). Every sync is a preview unless `--apply` is present.

```bash
python3 "$SKILL_DIR/scripts/env_manager.py" sync-shell --rcfile "$HOME/.zshenv"
python3 "$SKILL_DIR/scripts/env_manager.py" sync-shell --rcfile "$HOME/.zshenv" --apply
python3 "$SKILL_DIR/scripts/env_manager.py" audit
```

After applying zsh projection, verify in a new clean zsh process by checking presence or a fingerprint only; never print the value. `sync-system` targets the current user login session, not machine-wide state, and requires `--acknowledge-process-env-risk --apply`.

### Step 5: Use the local Dashboard

```bash
python3 "$SKILL_DIR/scripts/env_manager.py" dashboard --open
```

The Dashboard shows accounts, effective health, expiry windows, validation age, and target bindings. It can switch bindings and update administrative or validation status, but adding, reading, exporting, or deleting secret values remains terminal-only. See [references/dashboard.md](references/dashboard.md).

### Step 6: Report evidence

Report only:

- platform/account/key locators;
- variable names and selected targets;
- effective health, dates, validation age, and fingerprint when requested;
- files changed, their modes, backup path, and audit result;
- copyable `context_id` for errors.

Never report a raw Key, secret reference path, generated export content, or a command containing a secret.

## CLI Summary

| Command | Outcome |
| --- | --- |
| `init` | Create the registry and secure storage directory |
| `add` | Add one platform/account/key record and secret source |
| `list`, `show` | Return redacted inventory and effective health |
| `status`, `mark-validation` | Maintain administrative and validation state |
| `probe` | Validate one Key through a guarded HTTPS request |
| `bind`, `unbind` | Select the only Key used by a target variable |
| `sync-shell` | Preview or update generated zsh exports and `~/.zshenv` source block |
| `sync-system` | Preview or update current user session environment |
| `audit` | Detect unsafe permissions, dangling bindings, unhealthy selections, and expiry warnings |
| `dashboard` | Run the redacted local operations console |

All commands support `--json`. Mutating output names changed records but never secret values.

## Dependencies

- Python 3.9+ standard library.
- Optional macOS `security` command for Keychain storage.
- Optional 1Password CLI `op` for `op://` secret references.
- zsh for `sync-shell`; macOS `launchctl` or Linux `systemctl --user` for `sync-system`.

## Validation

```bash
python3 "$SKILL_DIR/scripts/validate_skill.py" "$SKILL_DIR"
python3 -m unittest discover -s "$SKILL_DIR/tests" -v
```

## 通用反馈闭环

用户在 Skill 驱动任务中提出修改意见时，继续当前产物前必须执行：

1. 先判断意见是 `task-specific`（仅本次）还是 `reusable`（可跨任务复用）。
2. `task-specific` 只修改当前任务，不改 Skill。
3. `reusable` 先确定作用域：领域规则先更新对应 canonical Skill；适用于所有 Skill 的规则先更新共享规范。
4. 完成规则更新、版本、lint 与分发核验后，再把修改应用到当前任务。
5. `reusable` 修改会使此前的“确认”“继续”“发吧”失效；完成当前产物修改和回读后必须停下，等待用户下一步指示，不自动进入发布、提交或其他外部写入。
