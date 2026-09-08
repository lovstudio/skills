---
name: lov-wxmp-cli
description: "微探命令行：检索微信公众号文章缓存，读取正文并导出 Markdown、HTML、JSON、CSV；按授权搜索和采集公众号。"
version: 0.1.1
depends_on:
  - lov-branding-consistency
---

# 微探命令行 · Weitan CLI

这是 LovStudio 的付费 Skill。安装加密运行包后，按账户已有权益解密使用；尚未拥有时，安装流程会先展示 Credits 兑换确认。

```bash
npx lovstudio skills add wxmp-cli
```

Agent 使用前先读取完整说明：

```bash
uvx lovstudio-skill-helper decrypt wxmp-cli
```

运行环境检查：

```bash
uvx lovstudio-skill-helper exec wxmp-cli scripts/wxmp_cli.py --json doctor
```

0.1.1：包含匹配的命令行与采集引擎，无需另行取得 app 源码。真实缓存读取、四种格式导出及相对路径输出已验证。在线搜索与采集需要有效登录，成功链路尚未现场验证。
