# sgc-clash-tun-doctor

![Version](https://img.shields.io/badge/version-0.2.0-CC785C)

基于最终运行态、实时连接和日志证据，诊断并修复 Clash Verge Rev TUN 导致的应用联网故障。

Independent source repository, also distributed through [lovstudio dev-skills](https://github.com/lovstudio/skills) — by [lovstudio.ai](https://lovstudio.ai)

## 适用场景

- 开启 TUN 后微信图片发不出去。
- 微信朋友圈图片加载很慢或完全不显示。
- 应用被错误规则送进失效代理，持续 Loading。
- 订阅中已经关闭 IPv6，但最终运行配置仍启用 IPv6。
- Mihomo 日志出现 `no route to host` 或 `context deadline exceeded`。

## Install

```bash
npx skills add lovstudio/clash-tun-doctor-skill
```

The aggregate bundle remains available:

```bash
npx skills add lovstudio/skills
```

或使用 Claude Code 插件市场：

```text
/plugin marketplace add lovstudio/skills
/plugin install dev-tools@sgc-dev
```

依赖：macOS、Clash Verge Rev、Python 3.8+。诊断 CLI 只使用 Python 标准库。

## Usage

```bash
SKILL_DIR="${LOVSTUDIO_SKILLS_INSTALL_DIR:?Set LOVSTUDIO_SKILLS_INSTALL_DIR}/sgc-clash-tun-doctor"

# 只读诊断
python3 "$SKILL_DIR/scripts/clash_tun_doctor.py" diagnose --app wechat

# 从运行连接和近期轮转日志生成 DIRECT 清单
python3 "$SKILL_DIR/scripts/clash_tun_doctor.py" direct-list \
  --app miracleplus \
  --host apply.miracleplus.com \
  --output ./miracleplus-direct.yaml

# 合并进当前规则并在线热加载，全程保持 Clash 运行
python3 "$SKILL_DIR/scripts/clash_tun_doctor.py" direct-list \
  --app miracleplus \
  --host apply.miracleplus.com \
  --apply

# 预演修复
python3 "$SKILL_DIR/scripts/clash_tun_doctor.py" fix-wechat

# 备份、修复、重启并验证
python3 "$SKILL_DIR/scripts/clash_tun_doctor.py" fix-wechat --apply

# 回滚最近一次修复
python3 "$SKILL_DIR/scripts/clash_tun_doctor.py" rollback --apply
```

## 安全模型

- 永远先诊断，后修改。
- 修改命令默认 dry-run，必须显式传入 `--apply`。
- 每次修改创建时间戳备份和文件映射清单。
- DIRECT 清单与现有 `prepend` 合并，不覆盖用户已有规则。
- 规则型修复通过 Mihomo Unix Socket 热加载，Clash Verge 保持运行。
- 不修改订阅 URL，不输出代理密钥或控制器 Secret。
- 修复后检查最终配置和 Mihomo 运行态，而不是只检查源配置。

## Options

| 参数 | 默认值 | 说明 |
|---|---|---|
| `--data-dir` | 自动发现 | Clash Verge Rev 数据目录。 |
| `--socket` | 自动发现 | Mihomo 控制器 Unix Socket。 |
| `--app` | `wechat` | 诊断时使用的应用过滤器。 |
| `--host` | — | 明确加入清单的域名，可重复传入。 |
| `--output` | — | 输出 Mihomo classical rule-provider YAML 清单。 |
| `--log-limit` | `4000` | 每段近期轮转日志读取的行数。 |
| `--apply` | false | 明确授权修改或回滚。 |
| `--no-reload` | false | 只持久化 DIRECT 清单，不热加载运行态。 |
| `--no-restart` | false | 修改后不重启 Clash Verge。 |
| `--json` | false | 输出 JSON 诊断结果。 |

## License

MIT
