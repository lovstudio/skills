# 修复手册

## 决策树

```text
provider 缺失
├── 该 provider 仍被某个入口使用（yoda、custom 这类稳定桶）
│   └── 分支 A：在 config.toml 补定义，保留历史桶身份
├── 该 provider 已退役（lovbrowser、nebula、实验命名等）
│   └── 分支 B：把历史 thread 重打标签到当前可用 provider
└── 无法确认
    └── 先分支 A（影响面更小），或对分支 B 先跑 dry-run 看范围
```

判断依据只来自诊断输出：thread 数量、最近使用时间、桌面日志里是否仍有新的 resume
失败。不要按 provider 名字猜用途。

## 分支 A：补定义

1. 生成片段（不会输出任何密钥值）：

```bash
python3 "$SKILL_DIR/scripts/codex_provider_doctor.py" \
  --print-provider-snippet yoda --like custom --env-key DEEPSEEK_API_KEY
```

2. 把片段粘贴进 `~/.codex/config.toml`，放在其他 `[model_providers.*]` 旁边。
   片段的 `base_url`、`name`、`wire_api` 来自 `--like` 指向的现有 provider。
3. 凭据二选一：
   - `env_key`：要求启动 App 的环境里存在该变量。GUI 启动的 App 通常读不到 shell
     环境变量，macOS 可用 `launchctl setenv` 或改用内联凭据。
   - 内联：与现有 provider 相同，把 `experimental_bearer_token` 写进该块（保持
     `chmod 600 ~/.codex/config.toml`）。不要把密钥提交进任何仓库。
4. 完全退出并重启 Codex 桌面 App（配置只在启动时读取）。
5. 复跑诊断，确认目标 provider 从缺失列表消失，并让用户实际打开一条目标会话。

注意：静态定义会在接入路线变化后过期。补定义时记录「这个块是兼容锚点」，路线变更
后同步更新，否则会从「打不开」变成「打开了但请求失败」。

## 分支 B：重打标签

1. 先 dry-run，确认范围和备份位置：

```bash
python3 "$SKILL_DIR/scripts/codex_provider_doctor.py" \
  --fix-retag custom --only-provider lovbrowser
```

2. 完全退出 Codex 桌面 App 后执行：

```bash
python3 "$SKILL_DIR/scripts/codex_provider_doctor.py" \
  --fix-retag custom --only-provider lovbrowser --yes
```

3. 工具会：
   - 用 SQLite 备份 API 复制一份完整 `state_5.sqlite`；
   - 更新 `threads.model_provider`；
   - 重写对应 rollout 首行 `session_meta.payload.model_provider`，并保留首行原文；
   - 打印更新数量、失败数量与剩余缺失 provider。

4. 大范围修复时：
   - `--active-only` 只处理未归档 thread；
   - `--skip-rollouts` 只改索引（结果里必须注明 rollout 尚未同步）；
   - 本机 3108 个受影响 rollout 合计约 17 GiB，全量重写需要时间，分批执行更稳。

## 回滚

```bash
python3 "$SKILL_DIR/scripts/codex_provider_doctor.py" \
  --restore ~/.codex/provider-repair-backups/<timestamp> --yes
```

备份目录包含 `state_5.sqlite` 与 `rollouts/` 下按原路径镜像的 `.firstline` 文件。
回滚会还原索引库与被改写 rollout 的首行；未被改写的文件不动。

## 验证清单

- [ ] 诊断输出里目标 provider 已不在缺失列表，或剩余项已写明原因。
- [ ] `--sample-rollouts` 抽样中没有 `index != rollout` 的不一致。
- [ ] 桌面 App 重启后能打开一条目标会话，不再出现 `invalid_config`。
- [ ] `codex resume <thread-id>` 能进入会话（CLI 侧同等验证）。
- [ ] 备份目录可读，回滚命令已经写进交付说明。
- [ ] 若走分支 A，`config.toml` 权限仍是 `600`，且没有把密钥带进仓库或日志。

## 常见坑

- **App 正在运行时直接写库**：WAL 由运行中的进程持有，工具会拒绝；先退出 App。
- **只改索引不改 rollout**：下次恢复可能被 session_meta 覆盖。
- **把仍在使用的 provider 改名**：集成方的历史过滤按 provider id 精确匹配，改名会让
  对方看不到自己的历史。
- **用 `--force` 跳过进程检查后忘记回读**：修复后一定要复跑诊断。
- **换版本后沿用旧结论**：`state_5.sqlite` 结构和日志字段随版本变化，升级后重跑只读诊断。
