# IPRoyal 链式出口 · IPRoyal Chain Exit

![Version](https://img.shields.io/badge/version-0.1.0-CC785C)

把 IPRoyal 静态住宅 IP 经 RayLink 的加密节点链式接入 Clash Verge Rev，让 AI 网站稳定走这个固定 IP；写入前可预览，写入后可验证、可移除、可回滚。

## 为什么不能直接用 IPRoyal

IPRoyal ISP 只提供明文 HTTP / SOCKS5 入口。从国内直连时，目标域名在明文里可见：被墙网站会被重置，随后约 90 秒连代理端口本身都连不上；没被墙的网站也会被 IPRoyal 随机拒绝一部分。挂到 RayLink 的加密节点后面就稳定了。详见 [`references/why-chain.md`](references/why-chain.md)。

## 安装

```bash
npx lovstudio skills add iproyal-raylink
```

本地源码安装：

```bash
ln -s "$(pwd)" "${SKILL_SKILLS_INSTALL_DIR:?请设置本地 Skills 目录}/lov-iproyal-raylink"
```

## 使用

对 Agent 说「把 IPRoyal 加入 RayLink」即可。手动运行：

```bash
export IPROYAL_PROXY='主机:端口:用户名:密码'      # IPRoyal 后台复制的字符串，在你自己的终端里设置
python3 scripts/iproyal_raylink.py detect          # 只读：找到 RayLink 配置
python3 scripts/iproyal_raylink.py apply           # 预览
python3 scripts/iproyal_raylink.py apply --apply --restart   # 写入并重启（macOS）
python3 scripts/iproyal_raylink.py verify          # 验证 AI 网站出口 IP
```

常用参数：

| 参数 | 默认 | 说明 |
| --- | --- | --- |
| `--carrier` | `TCP 稳定` | 承载 IPRoyal 的 RayLink 加密分组 |
| `--expose` | `RayLink 代理,AI 网站代理` | 列出 `IPRoyal 出口` 的分组 |
| `--select` | `AI 网站代理` | 排第一并被选为 `IPRoyal 出口` 的分组 |
| `--type` | `http` | `socks5` 时用 12324 端口 |
| `--wrap-existing` | 关 | 脚本已有自定义 `main` 时自动包装 |
| `--restart` | 关 | macOS 自动重启 Clash Verge 并设置选择 |

移除与回滚（默认都只预览）：

```bash
python3 scripts/iproyal_raylink.py remove --apply
python3 scripts/iproyal_raylink.py rollback --apply --restart
```

## 用户 Profile（跨 session）

在 `skill.yaml` 声明 `user-profile/v1`。只保存非敏感偏好（例如承载分组、默认选择）到 `skills.lov-iproyal-raylink.records`；IPRoyal 账号密码不进入 Profile。详见 [`references/user-profile.md`](references/user-profile.md)。

## 原子组合

单个 Skill；`lov-clash-tun-doctor` 是可选的下游诊断。见 [`references/skill-composition.md`](references/skill-composition.md)。

## 可信度卡与用户案例

- [`skill-card.yaml`](skill-card.yaml) / [`skill-card.md`](skill-card.md)
- [`cases/cases.json`](cases/cases.json)
- [`pricing-card.yaml`](pricing-card.yaml)

## 质量门

```bash
python3 scripts/validate_skill.py .
```

## 依赖

- Python 3.8+（仅标准库）
- 可选：PyYAML、node

## License

MIT
