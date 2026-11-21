# 共绩算力 CLI · Suanli CLI

![Version](https://img.shields.io/badge/version-0.1.0-CC785C)

在对话里安全地查询和操作共绩算力（suanli.cn）的 Open API 与大模型云服务，共 83 个接口。

- 随附由官方公开文档生成的 `lov-suanli-cli`、SDK 和本地 Swagger 代理；
- 默认只读，写操作和计费调用要逐次征得用户同意；
- 密钥只从环境变量或 macOS 钥匙串读取。

## 安装

```bash
npx lovstudio skills add gjkj-cli -g -y
```

本地源码安装（三层链接）：

```bash
ln -s "$(pwd)" ~/.agents/skills/lov-gjkj-cli
ln -s ../../.agents/skills/lov-gjkj-cli ~/.claude/skills/lov-gjkj-cli
```

## 准备密钥（用户本人执行）

```bash
security add-generic-password -U -a "$USER" -s suanli-token -w     # Open API 密钥
security add-generic-password -U -a "$USER" -s suanli-llm-key -w   # 大模型 API Key（可选）
python3 scripts/gjkj_cli.py doctor                                 # 只报长度，不显示密钥
```

## 用法

```bash
python3 scripts/gjkj_cli.py ops --group 存储                       # 列命令：W 写 · $ 计费 · E 加密 · V 已实测
python3 scripts/gjkj_cli.py run -- storage-get-regions             # 只读查询
python3 scripts/gjkj_cli.py run -- deployment-task-change-points --data '{"task_id":1,"points":2}' --dry-run
python3 scripts/gjkj_cli.py swagger --port 4790                    # 本地 Swagger，只监听 127.0.0.1
```

对话里可以这样说：「查一下共绩算力上我有哪些任务」「看看共绩这个月的账单」「打开共绩算力的 Swagger」。

## 用户 Profile

只记工作偏好：Swagger 端口、是否输出完整 envelope、常用区域。不保存密钥、账号或查询结果。详见 [`references/user-profile.md`](references/user-profile.md)。

## 质量门

```bash
python3 scripts/validate_skill.py .
python3 scripts/gjkj_cli.py doctor
```

## 依赖

Node.js 20+、Python 3.8+。接口有变化时，用 `lov-cli2anything` 的 suanli.cn 适配器重新生成，步骤见 [`references/regenerate.md`](references/regenerate.md)。

## License

MIT
