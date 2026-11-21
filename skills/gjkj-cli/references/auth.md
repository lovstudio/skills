# 认证与密钥

密钥只由用户本人在控制台创建、在自己的终端里输入；Agent 不代填、不复述、不写进任何文件或对话。

## 两种密钥

| 用途 | 在哪建 | 钥匙串条目 | 环境变量 |
| --- | --- | --- | --- |
| Open API（任务、存储、账单、裸金属） | 控制台「设置 → 密钥」https://console.suanli.cn/settings/key | `suanli-token` | `SUANLI_TOKEN` |
| 大模型云服务（`/v1/*`） | 控制台模型页 https://console.suanli.cn/models 的 API 密钥页（可设过期时间与额度） | `suanli-llm-key` | `SUANLI_LLM_API_KEY` |

团队账号下只有主账号和团队管理员能创建或删除 Open API 密钥，开发者角色只能用已有密钥。

## 存进钥匙串（macOS，用户自己执行）

```bash
security add-generic-password -U -a "$USER" -s suanli-token -w     # 提示输入两次，不回显；-U 覆盖已有条目
security add-generic-password -U -a "$USER" -s suanli-llm-key -w
```

存好后用 `gjkj_cli.py doctor` 核对：`keychain_length` 应是完整密钥的长度（几十个字符）。
个位数长度说明输错或只粘了一部分，让用户用同一条命令重存。环境变量优先于钥匙串；`SUANLI_KEYCHAIN=0` 关闭钥匙串回退。

## 两种签名模式

- **Token 模式**（默认）：请求头带 `token`、`version`（默认 1.0.0）、`timestamp`（毫秒）。
- **RSA 模式**：设置 `SUANLI_PRIVATE_KEY_FILE` 后自动启用，额外生成 `sign_str`（对 `path\nversion\ntimestamp\ntoken\nbody` 签名）。
- **加密请求体**：7 个标 `E` 的接口还需要平台公钥 `SUANLI_PLATFORM_PUBLIC_KEY_FILE`，请求体按 244 字节分段加密。

## 用户把密钥贴进了对话

立刻提醒：这把密钥已经出现在对话记录里，用完后到控制台删除并新建一把，新密钥用上面的钥匙串命令自己输入。
